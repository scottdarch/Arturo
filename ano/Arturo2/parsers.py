#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

import re

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
                    raise Exception("Molformed key=value pair in %s: %s" % (vendorFilePath, line))
                pair = [line[:firstEqual], line[firstEqual+1:].rstrip()];
                compoundKey = pair[0].split('.')
                value = pair[1]
                if menuHandler is not None and menuHandler.handleLine(line, pair[0], value):
                    if console is not None:
                        console.printVerbose("Found menu definition {}={}".format(pair[0], value))
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
    def expandMacros(cls, dictionary, key, rawValue, elideKeysForMissingValues=False, console=None):
        expanded = ""
        pos = 0
        match = ArduinoKeyValueParser.MACRO_PATTERN.search(rawValue, pos)
        while match is not None:
            pos = match.end()
            macroname = match.group(1)
            try :
                expansion = dictionary[macroname]
                expanded += rawValue[match.pos:match.start()] + expansion
                if console is not None:
                    console.printVerbose("found macro \"%s\" => \"%s\"" % (macroname, expansion))
            except KeyError:
                if elideKeysForMissingValues:
                    expanded += rawValue[match.pos:match.start()]
                else:
                    expanded += rawValue[match.pos:match.end()]
                if console is not None:
                    console.printVerbose("found macro \"%s\" => [no value]" % (macroname))
                
            match = ArduinoKeyValueParser.MACRO_PATTERN.search(rawValue, pos)
            
        expanded += rawValue[pos:]
        if console is not None:
            console.printVerbose("    raw      = %s" % (rawValue))
            console.printVerbose("    expanded = %s" % (expanded))
        
        dictionary[key] = expanded
        
        return expanded