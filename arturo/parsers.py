#  _____     _
# |  _  |___| |_ _ _ ___ ___
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

import distutils
import os
import re


# +---------------------------------------------------------------------------+
# | Makefile Property Parser
# +---------------------------------------------------------------------------+
class MakefilePropertyParser(object):
    '''
    Parses any simple name/value pairs found in a gnu makefile
    '''

    LINECOMMENT_PATTERN = re.compile("^\s?\#")
    ONLYWHITESPACE_PATTERN = re.compile("^\s+$")
    KEYVALUE_PATTERN = re.compile("(\S+)\s*[\?\:]?\=\s*(\S+)")

    def __init__(self):
        raise Exception("static only")

    @classmethod
    def parse(cls, makefilePath, mergeWith=dict(), console=None):
        with open(makefilePath) as makefile:
            for line in makefile:
                if len(line) is 0 or cls.ONLYWHITESPACE_PATTERN.match(line):
                    if console is not None:
                        console.printVerbose("Skipping empty line")
                    continue
                if cls.LINECOMMENT_PATTERN.match(line):
                    if console is not None:
                        console.printVerbose("Skipping comment %s" % (line))
                    continue
                kvmatch = cls.KEYVALUE_PATTERN.match(line)
                if kvmatch is not None:
                    mergeWith[kvmatch.group(1).lower()] = kvmatch.group(2)
        return mergeWith

# +---------------------------------------------------------------------------+
# | .gitignore Rule Parser
# +---------------------------------------------------------------------------+


class GitIgnoreParser(object):
    '''
    Collects all ignore rules from a .gitignore found in a provided path.
    '''

    LINECOMMENT_PATTERN = re.compile("^\s?\#")
    ONLYWHITESPACE_PATTERN = re.compile("^\s+$")

    def __init__(self):
        raise Exception("static only")

    @classmethod
    def parse(cls, basepath, ignoreRules=[]):
        ignorefile = os.path.join(basepath, ".gitignore")
        if os.path.isfile(ignorefile):
            with open(ignorefile) as gitignore:
                for line in gitignore:
                    if len(line) is 0 or cls.ONLYWHITESPACE_PATTERN.match(line):
                        continue
                    if cls.LINECOMMENT_PATTERN.match(line):
                        continue
                    ignoreRules.append(line.strip())
        return ignoreRules

# +---------------------------------------------------------------------------+
# | ArduinoKeyValueParser
# +---------------------------------------------------------------------------+


class ArduinoKeyValueDiscardMenuHandler(object):
    '''
    Menu handler for ArduinoKeyValueParser that simply discards all menu definitions.
    '''

    def handleLine(self, line, key, value):
        if (key.startswith("menu.")):
            return True
        else:
            return False


class ArduinoKeyValueParser(object):
    '''
    Parses "key=value" text files with special facilities for Arduino's configuration documents like
    boards.txt.
    '''
    LINECOMMENT_PATTERN = re.compile("^\s?\#")
    ONLYWHITESPACE_PATTERN = re.compile("^\s+$")
    MACRO_PATTERN = re.compile("(?<!\\\\){(\S*?)(?<!\\\\)}")

    def __init__(self):
        raise Exception("static only")

    @classmethod
    def parse(cls, vendorFilePath, vendorObjectCollection, vendorObjectFactory=None, menuHandler=ArduinoKeyValueDiscardMenuHandler(), console=None):

        with open(vendorFilePath) as vendorFile:
            for line in vendorFile:
                if len(line) is 0 or ArduinoKeyValueParser.ONLYWHITESPACE_PATTERN.match(line):
                    if console is not None:
                        console.printVerbose("Skipping empty line")
                    continue
                if ArduinoKeyValueParser.LINECOMMENT_PATTERN.match(line):
                    if console is not None:
                        console.printVerbose("Skipping comment %s" % (line))
                    continue
                firstEqual = line.find('=')
                if firstEqual == -1:
                    raise Exception(
                        "Malformed key=value pair in %s: %s" % (vendorFilePath, line))
                pair = [line[:firstEqual], line[firstEqual + 1:].rstrip()]
                compoundKey = pair[0].split('.')
                value = pair[1]
                if menuHandler is not None and menuHandler.handleLine(line, pair[0], value):
                    if console is not None:
                        console.printVerbose(
                            "Found menu definition {}={}".format(pair[0], value))
                    continue
                if vendorObjectFactory is not None:
                    key = compoundKey[0]
                    try:
                        vendorObject = vendorObjectCollection[key]
                    except KeyError:
                        vendorObject = vendorObjectFactory(key)
                        vendorObjectCollection[key] = vendorObject
                    vendorObject[pair[0][len(key) + 1:]] = value
                else:
                    key = pair[0]
                    vendorObjectCollection[key] = value
        return vendorObjectCollection

    @classmethod
    def expandMacros(cls, macroNamespace, lookupFunction, rawValue, elideKeysForMissingValues=False, console=None):
        expanded = ""
        pos = 0
        match = ArduinoKeyValueParser.MACRO_PATTERN.search(rawValue, pos)
        while match is not None:
            pos = match.end()
            macroname = match.group(1)
            try:
                expansion = lookupFunction(macroNamespace, macroname)
                expanded += rawValue[match.pos:match.start()] + expansion
                if console is not None:
                    console.printVerbose(
                        "found macro \"%s\" => \"%s\"" % (macroname, expansion))
            except KeyError:
                if elideKeysForMissingValues:
                    expanded += rawValue[match.pos:match.start()]
                else:
                    expanded += rawValue[match.pos:match.end()]
                if console is not None:
                    console.printVerbose(
                        "found macro \"%s\" => [no value]" % (macroname))

            match = ArduinoKeyValueParser.MACRO_PATTERN.search(rawValue, pos)

        expanded += rawValue[pos:]
        if console is not None:
            console.printVerbose("    raw      = %s" % (rawValue))
            console.printVerbose("    expanded = %s" % (expanded))

        return expanded

# +---------------------------------------------------------------------------+
# | InferLibraryDependenciesFromSourceParser
# +---------------------------------------------------------------------------+


class InferLibraryDependenciesFromSourceParser(object):
    '''
    Parses source files and builds library abstractions for inferred library dependencies. Mostly this is
    done by looking at include statements.
    '''

    def __init__(self, console):
        super(InferLibraryDependenciesFromSourceParser, self).__init__()
        self._console = console
        self._headerPattern = re.compile(
            '^\s*#include\s*[<"]\s*([a-zA-Z0-9_/\.\-]*)\s*[>"]')
        self._versionPattern = re.compile(
            '^(?P<name>\w+)\-(?P<major>\d+)(?:\.(?P<minor>\d+))?(?:\.(?P<patch>\d+))?$')
        self._blockCommentStartPattern = re.compile("/\*(?!.*\*/)")
        self._blockCommentEndPattern = re.compile("\*/")

    def getConsole(self):
        return self._console

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
                    isCommentedOut = False if self._blockCommentEndPattern.search(
                        line) else True
                    if console.willPrintVerbose():
                        lineMatch = self._headerPattern.search(line)
                        if lineMatch:
                            console.printVerbose(
                                "Ignoring commented out include " + lineMatch.get(1))
                else:
                    lineMatch = self._headerPattern.search(line)
                    if lineMatch:
                        nameAndVersion = self._headerToNameAndVersion(
                            lineMatch.group(1))
                        if nameAndVersion[0] not in included.keys():
                            included[nameAndVersion[0]] = nameAndVersion[1]
                        elif included[nameAndVersion[0]] != nameAndVersion[1]:
                            raise RuntimeError(
                                _("Two different versions of {} found when scanning headers.".format(nameAndVersion[1])))
                        included[nameAndVersion[0]] = nameAndVersion[1]
                        if console.willPrintVerbose():
                            console.printVerbose(
                                "Found include {} ({})".format(lineMatch.group(1), lineMatch.group(0)))
                    if self._blockCommentStartPattern.search(line):
                        isCommentedOut = True
        return included

    def getPossibleLibsForSource(self, configuration, filepath, excludeHeaderOnly=True):
        console = self.getConsole()
        included = self.findAllIncludesInFile(filepath)
        libraries = configuration.getLibraries()
        matchedLibs = dict()
        for name, version in included.iteritems():
            libraryVersionsMatch = libraries.get(name)
            if libraryVersionsMatch:

                if version:
                    libraryMatch = self._findCompatibleVersion(
                        libraryVersionsMatch, version)
                else:
                    libraryMatch = self._getNewestLibrary(libraryVersionsMatch)

                if libraryMatch:
                    if excludeHeaderOnly and not libraryMatch.hasSource():
                        console.printDebug(
                            "{} version {} is header only. Skipping".format(name, version))
                    else:
                        console.printVerbose(
                            "{} specified version {} of {}.".format(filepath, version, name))
                        matchedLibs[
                            libraryMatch.getNameAndVersion()] = libraryMatch
                else:
                    raise RuntimeError("{} depends on version {} of {} which was not found in the current environment."
                                       .format(filepath,
                                               version,
                                               name))
            elif console.willPrintVerbose():
                console.printVerbose(
                    "{} did not resolve to a know library for the current environment.".format(name))
        return matchedLibs

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _getNewestLibrary(self, libraryVersions):
        for libraryVersion in sorted(libraryVersions, distutils.version.LooseVersion, reverse=True):
            return libraryVersions[libraryVersion]

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
            match = self._versionPattern.match(
                pathelements[len(pathelements) - 2])
            if match:
                matchDict = match.groupdict()
                version = ""
                if 'name' in matchDict.keys() and matchDict['name'] == libraryname:
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
