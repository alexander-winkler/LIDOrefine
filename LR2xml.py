import re
from lxml import etree
import argparse
from pathlib import Path
import csv
import json


# PARSER
parser = argparse.ArgumentParser(
                    prog='LR2csv - Convert refined CSV back into a LIDO XML',
                    description='What the program does',
                    epilog='Text at the bottom of help')
parser.add_argument('-i', '--infile')
parser.add_argument('-x', '--xml')
parser.add_argument('-I', '--infix', nargs = "?", default = "_refined")

args = parser.parse_args()
filename = Path(args.infile)

if args.xml:
    xml_filename = Path(args.xml)
else:
    xml_filename = filename.with_suffix('.xml')


with open('mapping.json', 'r') as f:
  mapping = json.load(f)
  mapping2 = { v['parent'].split('/')[-1] : v['id'] for v in mapping.values()}

tree = etree.parse(xml_filename)
NSMAP = tree.getroot().nsmap

with open(filename, "r") as csvfile:
    reader = csv.DictReader(csvfile)
    for r in reader:
        location = r.get('location')
        field = location.split('/')[-1]
        
        element = tree.xpath(r.get('location'), namespaces = NSMAP)[0]
        IDs = element.xpath(mapping2[field], namespaces = NSMAP)

        for k,v in r.items():
            m = re.match('^(\d+) (\S+)$', k)
            if m:
                if v != "":
                    index = int(m.group(1))
                    if m.group(2) == "text":
                        IDs[index].text = v
                    else:
                        attribKey = m.group(2)
                        IDs[index].attrib[attribKey] = v


outputfilename = xml_filename.stem + args.infix + xml_filename.suffix

tree.write(outputfilename, encoding = "utf-8", xml_declaration = True)
