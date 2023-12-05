import re
from lxml import etree
import argparse
from pathlib import Path
import csv
import json


# PARSER
parser = argparse.ArgumentParser(
                    prog='LR2csv - Convert refined CSV back into a LIDO XML',
                    description='Takes a CSV (generated with LR2csv.py and enriched using, e.g. OpenRefine), the original LIDO XML and writes the modifications into a new LIDO XML file'
                    )
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
    dialect = csv.Sniffer().sniff(csvfile.readline(), [',',';'])
    csvfile.seek(0)
    reader = csv.DictReader(csvfile, delimiter = dialect.delimiter)
    for r in reader:
        location = r.get('location')
        field = location.split('/')[-1]
        splitTag = mapping2[field].split(':')
        tag = f"{{{NSMAP.get(splitTag[0])}}}{splitTag[1]}"
        
        IDelements = tree.xpath(r.get('location') + "/" + mapping2[field], namespaces = NSMAP)


        modifiedElements = dict()

        for k,v in r.items():
            m = re.match('^(\d+) (\S+)$', k)
            v = v.strip()
            if m:
                if v != "":

                    index = int(m.group(1))
                    if not index in modifiedElements:
                        modifiedElements[index] = etree.Element(tag)
                    
                    if m.group(2) == "text":
                        modifiedElements[index].text = v
                    else:
                        modifiedElements[index].attrib[m.group(2)] = v

        for n, elem in enumerate(IDelements):
            if modifiedElements.get(n) is not None:
                IDelements[n].getparent().replace(IDelements[n],modifiedElements.pop(n))
            else:
                print(n)

        for elem in modifiedElements.values():
            xpath = r.get('location') + "/" + mapping2[field] + "[last()]"
            tree.xpath(xpath, namespaces = NSMAP)[0].getparent().insert(n + 1, elem)
            n += 1

outputfilename = xml_filename.stem + args.infix + xml_filename.suffix

tree.write(outputfilename, encoding = "utf-8", xml_declaration = True)
print(outputfilename, " written.")
