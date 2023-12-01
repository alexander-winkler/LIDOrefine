from lxml import etree
import csv
import argparse
import re
from natsort import natsorted
from pathlib import Path
import json

with open('mapping.json', 'r') as f:
  mapping = json.load(f)

# PARSER
parser = argparse.ArgumentParser(
                    prog='LR2csv - Convert LIDO to CSV for Refinement',
                    description='Takes a LIDO XML and converts selected fields into a CSV file that can be modified using, e.g. OpenRefine.')


parser.add_argument('-a', action = "store", nargs = '?', default = 0, const = True, type = int, help = 'enrich actor fields')
parser.add_argument('-p', action = "store", nargs = '?', default = 0, const = True, type = int, help = 'enrich place fields')
parser.add_argument('-i', '--infile', required = True)
parser.add_argument('-o', '--outfile', required = False)
parser.add_argument('-d', '--targetdir', help = "specify the target dir" )



# Read Input
args = parser.parse_args()
filename = Path(args.infile)


tree = etree.parse(filename)
NSMAP = tree.getroot().nsmap

outputCollector = []

def convert(subdict, additionalElements):
    parentList = tree.findall(subdict['parent'], NSMAP)
    outputList = []
    for _ in parentList:
        location = tree.getpath(_)
        string = _.xpath(subdict['string'], namespaces = NSMAP)[0]
        IDs = _.xpath(subdict['id'], namespaces = NSMAP)
        IDs = [ dict(text = _.text) | dict(_.attrib) for _ in IDs]
        output = dict(location = location, string = string)
        keys = []
        i = 0
        for n, _ in enumerate(IDs, start = i):
            for k,v in _.items():
                keys.append(k)
                key = f"{n} {k}"
                output[key] = v
            i = n
        keys = set(keys)
        i += 1
        for x in range(i, i + additionalElements + 1):
            for k in keys:
                output[f"{x} {k}"] = ""
        outputList.append(output)
    return outputList

if args.a:
    outputCollector.extend(convert(mapping['a'], args.a))

if args.p:
    outputCollector.extend(convert(mapping['p'], args.p))


fieldnames = []
for row in outputCollector:
    fieldnames.extend(row.keys())
    fieldnames = natsorted(set(fieldnames))
    fieldnames = fieldnames[-2:] + fieldnames[:-2]

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
