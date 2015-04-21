#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

import re


class KeyValueParser(object):
    
    LINECOMMENT_PATTERN = re.compile("^\s?\#")
    ONLYWHITESPACE_PATTERN = re.compile("^\s+$")
    MACRO_PATTERN = re.compile("(?<!\\\\){(\S*?)(?<!\\\\)}")
    
    def __init__(self):
        raise Exception("static only")
    
    @classmethod
    def parse(cls, vendorFilePath, vendorObjectCollection, vendorObjectFactory=None, console=None):
        
        with open(vendorFilePath) as vendorFile:
            for line in vendorFile:
                if len(line) is 0 or KeyValueParser.ONLYWHITESPACE_PATTERN.match(line):
                    if console is not None:
                        console.printVerbose("Skipping empty line")
                    continue
                if KeyValueParser.LINECOMMENT_PATTERN.match(line):
                    if console is not None:
                        console.printVerbose("Skipping comment %s" % (line))
                    continue
                firstEqual = line.find('=')
                if firstEqual == -1:
                    raise Exception("Molformed key=value pair in %s: %s" % (vendorFilePath, line))
                pair = [line[:firstEqual], line[firstEqual+1:].rstrip()];
                compoundKey = pair[0].split('.')
                value = pair[1]
                
                if vendorObjectFactory:
                    try:
                        vendorObject = vendorObjectCollection[compoundKey[0]]
                    except KeyError:
                        vendorObject = vendorObjectFactory(compoundKey[0])
                        vendorObjectCollection[compoundKey[0]] = vendorObject
                    vendorObject[pair[0][len(compoundKey[0]) + 1:]] = value
                else:
                    vendorObjectCollection[pair[0]] = value
        return vendorObjectCollection

    @classmethod
    def expandMacros(cls, dictionary, key, rawValue, elideKeysForMissingValues=False, console=None):
        expanded = ""
        pos = 0
        match = KeyValueParser.MACRO_PATTERN.search(rawValue, pos)
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
                
            match = KeyValueParser.MACRO_PATTERN.search(rawValue, pos)
            
        expanded += rawValue[pos:]
        if console is not None:
            console.printVerbose("    raw      = %s" % (rawValue))
            console.printVerbose("    expanded = %s" % (expanded))
        
        dictionary[key] = expanded
        
        return expanded