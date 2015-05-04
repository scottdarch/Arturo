#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

import os
import re

from ano.Arturo2.commands.base import ConfiguredCommand, mkdirs

# +---------------------------------------------------------------------------+
# | Preprocess
# +---------------------------------------------------------------------------+
class Preprocess(ConfiguredCommand):
    """
    Preprocess an .ino sketch file and produce ready-to-compile .cpp source.

    Arturo mimics steps that are performed by official Arduino Software to
    produce similar result:

        * #include <Arduino.h> is prepended
        * Function _prototypes are added at the beginning of file
    """
    def __init__(self, environment, project, configuration, console):
        super(Preprocess, self).__init__(environment, project, configuration, console)

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
                lines = sketch.split('\n')
                includes, lines = self._extract_includes(lines)
        
                header = 'Arduino.h'
                out.write('#include <%s>\n' % header)
        
                out.write('\n'.join(includes))
                out.write('\n')
        
                out.write('\n'.join(prototypes))
                out.write('\n')
        
                out.write('#line 1 "%s"\n' % sketch)
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
