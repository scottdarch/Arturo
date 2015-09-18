#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

import distutils.version
import os
import re

from arturo import i18n
from arturo.commands.base import ConfiguredCommand, mkdirs, Command
from arturo.libraries import Library


_ = i18n.language.ugettext

# +---------------------------------------------------------------------------+
# | Cmd_preprocess
# +---------------------------------------------------------------------------+
class Cmd_preprocess(ConfiguredCommand):
    """
    Cmd_preprocess an .ino sketch file and produce ready-to-compile .cpp source.

    Arturo mimics steps that are performed by official Arduino Software to
    produce similar result:

        * #include <Arduino.h> is prepended
        * Function _prototypes are added at the beginning of file
    """
    def __init__(self, environment, project, configuration, console):
        super(Cmd_preprocess, self).__init__(environment, project, configuration, console)

        # single-quoted character
        p = "('.')"
        
        # double-quoted string
        p += "|(\"(?:[^\"\\\\]|\\\\.)*\")"
        
        # single and multi-line comment
        p += "|(//.*?$)|(/\\*[^*]*(?:\\*(?!/)[^*]*)*\\*/)"
        
        # pre-processor directive
        p += "|" + "(^\\s*#.*?$)"

        self._re_extension = re.compile(r'\.(\w+)\Z')
        self._re_strip = re.compile(p, re.MULTILINE)
        self._re_prototype = re.compile("[\\w\\[\\]\\*]+\\s+[&\\[\\]\\*\\w\\s]+\\([&,\\[\\]\\*\\w\\s]*\\)(?=\\s*\\{)")
        self._re_includes = re.compile("^\\s*#include\\s*[<\"](\\S+)[\">]")
        
        self._sketches = None
        self._outputDir = None

    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('Transform an Arduino sketch (ino) into valid cpp.'))

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        parser.add_argument("--output_dir", default=self.getConfiguration().getBuilddir())
        parser.add_argument("--sketch", nargs="+")

    def onVisitArgs(self, args):
        self._sketches = args.sketch
        self._outputDir = args.output_dir

    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        mkdirs(self._outputDir)
        for sketch in self._sketches:
            self._generateSFile(sketch, self._outputDir)
    
    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _generateSFile(self, sketch, outputPath):
        sketchBasename = os.path.basename(sketch)
        hasExt = self._re_extension.search(sketchBasename)
        if hasExt is not None:
            sketchBasename = sketchBasename[:hasExt.start(0)]

        outputFile = os.path.join(outputPath, sketchBasename + ".cpp")
        
        with open(outputFile, 'wt') as out:
    
            with open(sketch, 'rt') as sketchFile:
                sketch = sketchFile.read()
                prototypes = self._prototypes(sketch)
                #TODO: handle windows line endings, optionally.
                lines = sketch.split('\n')
                includes, lines = self._extract_includes(lines)
        
                header = 'Arduino.h'
                out.write('#include <%s>\n' % header)
        
                out.write('\n'.join(includes))
                out.write('\n')
        
                out.write('\n'.join(prototypes))
                out.write('\n')
        
                out.write('// line 1 %s\n' % sketch)
                out.write('\n'.join(lines))

    def _prototypes(self, src):
        src = self._collapse_braces(self._strip(src))
        matches = self._re_prototype.findall(src)
        return [m + ';' for m in matches]

    def _extract_includes(self, src_lines):
        includes = []
        sketch = []
        for line in src_lines:
            match = self._re_includes.match(line)
            if match:
                includes.append(line)
                # if the line is #include directive it should be
                # commented out in original sketch so that
                #  1) it would not be included twice
                #  2) line numbers will be preserved
                sketch.append('//' + line)
            else:
                sketch.append(line)

        return includes, sketch

    def _collapse_braces(self, src):
        """
        Remove the contents of all top-level curly brace pairs {}.
        """
        result = []
        nesting = 0;

        for c in src:
            if not nesting:
                result.append(c)
            if c == '{':
                nesting += 1
            elif c == '}':
                nesting -= 1
                result.append(c)
        
        return ''.join(result)

    def _strip(self, src):
        """
        Strips comments, pre-processor directives, single- and double-quoted
        strings from a string.
        """
        return self._re_strip.sub(' ', src)

# +---------------------------------------------------------------------------+
# | Cmd_source_headers
# +---------------------------------------------------------------------------+
class Cmd_source_headers(ConfiguredCommand):
    
    def getAllHeaders(self):
        configuration = self.getConfiguration()
        headers = configuration.getHeaders()
        core = configuration.getBoard().getCore()
        headers += core.getHeaders()
        variant = configuration.getBoard().getVariant()
        headers += variant.getHeaders()

        return headers

    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('Emit a list of headers suitable for consumption by gnu make.'))

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        None

    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        headers = self.getAllHeaders()

        projectPath = self.getProject().getPath()
        
        headerFolders = set()
        for header in headers:
            headerFolders.add(os.path.relpath(os.path.dirname(header), projectPath))
        self.getConsole().stdout(*headerFolders)
        
# +---------------------------------------------------------------------------+
# | Cmd_source_files
# +---------------------------------------------------------------------------+
class Cmd_source_files(ConfiguredCommand):
    
    def __init__(self, environment, project, configuration, console):
        super(Cmd_source_files, self).__init__(environment, project, configuration, console)
        self._sources = None
        
    def getAllSources(self):
        if self._sources is None:
            sources = self.getConfiguration().getSources()
            projectPath = self.getProject().getPath()
            self._sources = [os.path.relpath(sources[x], projectPath).strip() for x in range(len(sources))]
        return self._sources

    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('Emit a list of source files suitable for consumption by gnu make.'))

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        None
    
    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        self.getConsole().stdout(*self.getAllSources())

# +---------------------------------------------------------------------------+
# | Cmd_lib_source_files
# +---------------------------------------------------------------------------+
class Cmd_lib_source_files(ConfiguredCommand):

    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    @classmethod
    def appendCommandTemplateForClass(cls, inoutTemplates):
        return Command.appendCommandHelper(cls, 
                { 
                    'library'     : '--library',
                }, inoutTemplates)
        
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('Emit a list of source files for a given library suitable for consumption by gnu make.'))

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        parser.add_argument("-l", "--library", required=True)
    
    def onVisitArgs(self, args):
        setattr(self, "_library", args.library)
    
    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        libraries = self.getConfiguration().getLibraries()
        libNameAndVersion = Library.libNameAndVersion(self._library)
        libraryVersions = libraries.get(libNameAndVersion[0])
        if not libraryVersions:
            raise RuntimeError(_("No library with name {} was found.".format(libNameAndVersion[0])))
        library = libraryVersions.get(libNameAndVersion[1])
        if not library:
            raise RuntimeError(_("Version {} of library {} was not available.".format(libNameAndVersion[1], libNameAndVersion[0])))
        self.getConsole().stdout(*library.getSources())

# +---------------------------------------------------------------------------+
# | Cmd_lib_source_headers
# +---------------------------------------------------------------------------+
class Cmd_lib_source_headers(ConfiguredCommand):

    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    @classmethod
    def appendCommandTemplateForClass(cls, inoutTemplates):
        return Command.appendCommandHelper(cls, 
                { 
                    'library'     : '--library',
                }, inoutTemplates)
        
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('Emit a list of header files for a given library suitable for consumption by gnu make.'))

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        parser.add_argument("-l", "--library", required=True)
    
    def onVisitArgs(self, args):
        setattr(self, "_library", args.library)
    
    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        configuration = self.getConfiguration()

        libraries = configuration.getLibraries()
        libNameAndVersion = Library.libNameAndVersion(self._library)
        libraryVersions = libraries.get(libNameAndVersion[0])
        if not libraryVersions:
            raise RuntimeError(_("No library with name {} was found.".format(libNameAndVersion[0])))
        library = libraryVersions.get(libNameAndVersion[1])
        if not library:
            raise RuntimeError(_("Version {} of library {} was not available.".format(libNameAndVersion[1], libNameAndVersion[0])))

        headers = set(library.getHeaders(dirnameonly=True))
        dependantLibs = self._findAllLibrariesForLibrary(library)
        for dependantLib in dependantLibs.itervalues():
            headers.update(set(dependantLib.getHeaders(dirnameonly=True)))
        core = configuration.getBoard().getCore()
        headers.update(set(core.getHeaders(dirnameonly=True)))
        variant = configuration.getBoard().getVariant()
        headers.update(set(variant.getHeaders(dirnameonly=True)))

        self.getConsole().stdout(*headers)

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _findAllLibrariesForLibrary(self, library):
        if hasattr(self, "_libdeps"):
            return self._libdeps

        cmd_source_libs = self.getCommand("Cmd_source_libs")
        setattr(self, "_libdeps", cmd_source_libs.findAllLibrariesForLibrary(library))
        return self._libdeps

# +---------------------------------------------------------------------------+
# | Cmd_source_libs
# +---------------------------------------------------------------------------+
class Cmd_source_libs(Cmd_source_headers, Cmd_source_files):
    def __init__(self, environment, project, configuration, console):
        super(Cmd_source_headers, self).__init__(environment, project, configuration, console)
        self._headerPattern = re.compile('^\s*#include\s*[<"]\s*([a-zA-Z0-9_/\.\-]*)\s*[>"]')
        self._versionPattern = re.compile('^(?P<name>\w+)\-(?P<major>\d+)(?:\.(?P<minor>\d+))?(?:\.(?P<patch>\d+))?$')
        self._blockCommentStartPattern = re.compile("/\*(?!.*\*/)")
        self._blockCommentEndPattern = re.compile("\*/")
        self._libdeps = None
        
    def findAllIncludesInFile(self, filepath):
        '''
        Returns a dictionary of library names to version number.
        '''
        included = dict() 
        console = self.getConsole()
        console.printVerbose("Looking for includes in " + filepath)
        with open(filepath, 'r') as filehd:
            isCommentedOut = False
            for line in filehd:
                if isCommentedOut:
                    isCommentedOut = False if self._blockCommentEndPattern.search(line) else True
                    if console.willPrintVerbose():
                        lineMatch = self._headerPattern.search(line)
                        if lineMatch:
                            console.printVerbose("Ignoring commented out include " + lineMatch.get(1))
                        
                else:
                    lineMatch = self._headerPattern.search(line)
                    if lineMatch:
                        nameAndVersion = self._headerToNameAndVersion(lineMatch.group(1))
                        if not included.has_key(nameAndVersion[0]):
                            included[nameAndVersion[0]] = nameAndVersion[1]
                        elif included[nameAndVersion[0]] != nameAndVersion[1]:
                            raise RuntimeError(_("Two different versions of {} found when scanning headers.".format(nameAndVersion[1])))
                        included[nameAndVersion[0]] = nameAndVersion[1]
                        if console.willPrintVerbose():
                            console.printVerbose("Found include {} ({})".format(lineMatch.group(1), lineMatch.group(0)))
                    if self._blockCommentStartPattern.search(line):
                        isCommentedOut = True
        return included
                        
    def getPossibleLibsForSource(self, filepath, excludeHeaderOnly=True):
        console = self.getConsole()
        included = self.findAllIncludesInFile(filepath)
        libraries = self.getConfiguration().getLibraries()
        matchedLibs = dict()
        for name, version in included.iteritems():
            libraryVersionsMatch = libraries.get(name)
            if libraryVersionsMatch:
                
                if version:
                    libraryMatch = self._findCompatibleVersion(libraryVersionsMatch, version)
                else:
                    libraryMatch = self._getNewestLibrary(libraryVersionsMatch)
                    
                if libraryMatch:
                    if excludeHeaderOnly and not libraryMatch.hasSource():
                        console.printDebug("{} version {} is header only. Skipping".format(name, version))
                    else:
                        console.printVerbose("{} specified version {} of {}.".format(filepath, version, name))
                        matchedLibs[libraryMatch.getNameAndVersion()] = libraryMatch
                else:
                    raise RuntimeError("{} depends on version {} of {} which was not found in the current environment."
                                           .format(filepath, 
                                                   version, 
                                                   name))
            elif console.willPrintVerbose():
                console.printVerbose("{} did not resolve to a know library for the current environment.".format(name))
        return matchedLibs
    
    def getAllPossibleLibsForProject(self):
        if self._libdeps is not None:
            return self._libdeps
        
        self._libdeps = dict()
        sources = self.getAllSources()
        for source in sources:
            self._libdeps.update(self.getPossibleLibsForSource(source))
        headers = self.getAllHeaders()
        for header in headers:
            self._libdeps.update(self.getPossibleLibsForSource(header))
        
        directLibDeps = self._libdeps.copy()
        for libdep in directLibDeps.itervalues():
            self._findAllLibrariesRecursive(libdep, self._libdeps)
        return self._libdeps

    def findAllLibrariesForLibrary(self, library):
        results = dict()
        self._findAllLibrariesRecursive(library, results)
        return results;

    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        libdeps = self.getAllPossibleLibsForProject()
        #TODO: find recursive library dependencies (i.e. libraries that depend on other libraries).
        console = self.getConsole()
        if console.willPrintDebug():
            console.printDebug("Project {} has {} library dependencies".format(self.getProject().getName(), len(libdeps)))
        console.stdout(*libdeps)
            
    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _headerToNameAndVersion(self, headerPath):
        '''
        parses headers with path prefixes into library name and version. For example
        foobar-2.0/foobar.h -> ('foobar', '2.0')
        baz-2.0/foobar.h -> ('foobar', None)
        foobar.h -> ('foobar', None)
        foobar/baz.h -> ('baz', None)
        '''
        pathelements = headerPath.split('/')
        headername = pathelements[len(pathelements) - 1]
        lastdot = headername.rfind('.')
        libraryname = headername[:lastdot] if lastdot != -1 else headername
        if len(pathelements) > 1:
            match = self._versionPattern.match(pathelements[len(pathelements) - 2])
            if match:
                matchDict = match.groupdict()
                version = ""
                if matchDict.has_key('name') and matchDict['name'] == libraryname:
                    major = matchDict.get('major')
                    if major:
                        version += major
                        minor = matchDict.get('minor')
                        if minor:
                            version += "." + minor
                            patch = matchDict.get('patch')
                            if patch:
                                version += '.' + patch
            else:
                version = None
            
            return (libraryname, version)
        else:
            return (libraryname, None)
        
    def _findAllLibrariesRecursive(self, library, libdeps):
        console = self.getConsole()
        libraryHeaders = library.getHeaders()
        for header in libraryHeaders:
            headerLibDeps = self.getPossibleLibsForSource(header)
            before = len(libdeps)
            libdeps.update(headerLibDeps)
            if len(libdeps) > before:
                for headerLibDep in headerLibDeps.itervalues():
                    if console.willPrintVerbose():
                        console.printVerbose("Library {} depends on library {}".format(library.getName(), headerLibDep.getName()))
                    self._findAllLibrariesRecursive(headerLibDep, libdeps)
        librarySources = library.getSources()
        for source in librarySources:
            sourceLibDeps = self.getPossibleLibsForSource(source)
            before = len(libdeps)
            libdeps.update(sourceLibDeps)
            if len(libdeps) > before:
                for sourceLibDep in sourceLibDeps.itervalues():
                    if console.willPrintVerbose():
                        console.printVerbose("Library {} depends on library {}".format(library.getName(), sourceLibDep.getName()))
                    self._findAllLibrariesRecursive(sourceLibDep, libdeps)
        
    def _getNewestLibrary(self, libraryVersions):
        for libraryVersion in sorted(libraryVersions, distutils.version.LooseVersion, reverse=True):
            return libraryVersions[libraryVersion]
        
    def _findCompatibleVersion(self, libraryVersions, requestedVersion):
        '''
        Finds the best match based on major version only.
        '''
        # TODO: implement version sort cache
        requestedMajor = int(requestedVersion.split('.')[0])
        for libraryVersion in sorted(libraryVersions, distutils.version.LooseVersion, reverse=True):
            if requestedMajor <= int(libraryVersion.split('.')[0]):
                return libraryVersions[libraryVersion]
        return None
                
        
# +---------------------------------------------------------------------------+
# | Cmd_mkdirs
# +---------------------------------------------------------------------------+
class Cmd_mkdirs(ConfiguredCommand):
    '''
    portable version of mkdir -p
    '''
    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('portable version of mkdir -p'))

    @classmethod
    def appendCommandTemplateForClass(cls, inoutTemplates):
        return Command.appendCommandHelper(cls, 
                { 
                    'path'     : '--path',
                }, inoutTemplates)

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        parser.add_argument("--path")

    def onVisitArgs(self, args):
        self._path = getattr(args, "path")

    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        mkdirs(self._path)

# +---------------------------------------------------------------------------+
# | Cmd_d_to_p
# +---------------------------------------------------------------------------+
class Cmd_d_to_p(ConfiguredCommand):
    '''
    This is a portable version of the dependency scheme used by Automake.
    see http://make.mad-scientist.net/papers/advanced-auto-dependency-generation/ for details on this command.
    '''
    
    PFILE_EXTENSION = "dp"
    LIBDEP_EXTENSION = "a"
    
    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('convert a gnu .d file into Arturo dependencies.'))

    @classmethod
    def appendCommandTemplateForClass(cls, inoutTemplates):
        return Command.appendCommandHelper(cls, 
                { 
                    'dp_file_path'     : '--dpath',
                    'pfile_ext'        : cls.PFILE_EXTENSION,
                }, inoutTemplates)
    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        parser.add_argument("--dpath")
        parser.add_argument("--ppath", default=None)

    def onVisitArgs(self, args):
        self._dpath = getattr(args, "dpath")
        self._ppath = getattr(args, "ppath")

    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        dpath = self._dpath
        if not os.path.isfile(dpath):
            raise RuntimeError("{} was not found.".format(dpath))
        ppath = re.sub("\.d$", '.' + Cmd_d_to_p.PFILE_EXTENSION, dpath) if self._ppath is None else self._ppath
        removecommentsPattern = re.compile("^\s*#.*")
        removeLineContinuations = re.compile("\s*\\\\?\n$")
        isempty = re.compile("^$")
        buildTarget = None
        with open(ppath, "w") as pfile:
            with open(dpath, "r") as dfile:
                for line in dfile:
                    pfile.write(line)

            with open(dpath, "r") as dfile:
                for line in dfile:
                    # Find the first recipe line in the .d file and 
                    # save the build target for later dependency generation.
                    # reset the line to the target's dependencies and continue.
                    if buildTarget is None:
                        recipe = line.split(":")
                        if len(recipe) == 2:
                            buildTarget = recipe[0]
                            line = recipe[1]

                    items = line.split(' ')
                    for item in items:
                        item = removecommentsPattern.sub("", item)
                        item = removeLineContinuations.sub("", item)
                        if not isempty.match(item):
                            pfile.write(item + ":\n")
        
    def _getLibDeps(self, ppath):
        libnames = []
        endswithColon = re.compile("\:$")
        with open(ppath, "r") as pfile:
            possibleLibraryDependencies = dict()
            for line in pfile:
                if endswithColon.search(line):
                    nameAndVersion = Library.libNameAndVersion(os.path.basename(os.path.dirname(os.path.realpath(line[:-1]))))
                    if nameAndVersion in possibleLibraryDependencies:
                        versions = possibleLibraryDependencies[nameAndVersion[0]]
                    else:
                        versions = set()
                        possibleLibraryDependencies[nameAndVersion[0]] = versions
                    versions.add(nameAndVersion[1])

        libraries = self.getConfiguration().getLibraries()
        for libname, library in libraries.iteritems():
            if libname in possibleLibraryDependencies:
                versions = possibleLibraryDependencies[libname]
                if len(versions) > 1:
                    raise RuntimeError(_("{} required {} different versions of the {} library.".format(os.path.basename(ppath), len(versions), libname)))
                libnames.append("{}.{}".format(Library.libNameFromNameAndVersion(library.getName(), versions.pop()), self.LIBDEP_EXTENSION))
        return libnames;
