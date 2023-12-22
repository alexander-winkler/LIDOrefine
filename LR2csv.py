from lxml import etree
import csv
import argparse
import re
from natsort import natsorted
from pathlib import Path
import json
import sys

with open('mapping.json', 'r') as f:
  mapping = json.load(f)

# PARSER
parser = argparse.ArgumentParser(
                    prog='LR2csv - Convert LIDO to CSV for Refinement',
                    description='Takes a LIDO XML and converts selected fields into a CSV file that can be modified using, e.g. OpenRefine.')


parser.add_argument('-a', action = "store", nargs = '?', default = 0, const = True, type = int, help = 'enrich actor fields')
parser.add_argument('-p', action = "store", nargs = '?', default = 0, const = True, type = int, help = 'enrich place fields')
parser.add_argument('-s', action = "store", nargs = '?', default = 0, const = True, type = int, help = 'enrich subject fields')
parser.add_argument('-i', '--infile', required = True)
parser.add_argument('-o', '--outfile', required = False)
parser.add_argument('-d', '--targetdir', help = "specify the target dir" )



# Read Input
args = parser.parse_args()
filename = Path(args.infile)

try:
    tree = etree.parse(filename)
    NSMAP = tree.getroot().nsmap
except Exception as e:
    print(f"There was a problem with parsing the XML input file {filename}. Make sure the file is a proper XML file.")
    sys.exit(1)

outputCollector = []

def convert(subdict, additionalElements):
    parentList = tree.findall(subdict['parent'], NSMAP) # actor/place/objectWorktype/subjectConcept
    outputList = []
    for _ in parentList:
        location = tree.getpath(_) # xPath zum Feld
        string = _.xpath(subdict['string'], namespaces = NSMAP)[0]
        keys = ["{http://www.lido-schema.org}type", "{http://www.lido-schema.org}source", "text"]
        
        _IDs = _.xpath(subdict['id'], namespaces = NSMAP)
        IDs = []
        for _ in _IDs:
            attributes = dict.fromkeys(keys, "")
            attributes['text'] = _.text
            attributes.update(_.attrib)
            IDs.append(attributes)

        #IDs = [ dict(text = _.text) | dict(_.attrib) for _ in IDs]
        output = dict(location = location, string = string)
        
        # iterate over ID-elements
        i = 0
        for n, _ in enumerate(IDs):
            for k,v in _.items():
                keys.append(k)
                key = f"{n} {k}"
                output[key] = v
                i += n
        keys = set(keys)
        # add n additional (empty) Columns
        for x in range(i +1 , i + additionalElements + 1):
            for k in keys:
                if not f"{x} {k}" in output:
                    output[f"{x} {k}"] = ""
        outputList.append(output)
    return outputList

if args.a:
    outputCollector.extend(convert(mapping['a'], args.a))

if args.p:
    outputCollector.extend(convert(mapping['p'], args.p))

if args.s:
    outputCollector.extend(convert(mapping['s'], args.s))

if args.outfile:
    outputCollector.extend(convert(mapping['o'], args.outfile))


fixColumns = ["location", "string"] # first two columns

fieldnames = []
for row in outputCollector:
    fieldnames.extend(row.keys())
    fieldnames = [_ for _ in fieldnames if not _ in fixColumns]
    fieldnames = natsorted(set(fieldnames))
    fieldnames = fixColumns + fieldnames

if args.outfile: 
    outputFilename = Path(args.outfile)
else:
    outputFilename = Path(filename.stem + ".csv")

if args.targetdir:
    targetdir = Path(args.targetdir)
    targetdir.mkdir(exist_ok = True)
    outputFilename = targetdir / outputFilename.name


with open(outputFilename, "w") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
    writer.writeheader()
    writer.writerows(outputCollector)
    print(f"CSV written to {outputFilename}")
