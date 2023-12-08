import re
from lxml import etree
import argparse
from pathlib import Path
import csv
import json
import sys


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
    if not xml_filename.is_file():
        xml_filename = Path(str(xml_filename).replace("-csv",""))
        print(f"No file named {xml_filename} found, try {xml_filename} instead.")


with open('mapping.json', 'r') as f:
  # Schreibt Mapping-Dict um in die Form
  # {
  #   <PARENT-TAG(ohne Namespace)> : <ID-FELD IN Q-NOTATION>
  # }
  mapping = json.load(f)
  mapping2 = { v['parent'].split('/')[-1] : v['id'] for v in mapping.values()}

try:
    tree = etree.parse(xml_filename)
    NSMAP = tree.getroot().nsmap
except OSError as e:
    print(f"The original input XML could not be found. Provide the correct file name using the -x/--xml option.")
    print(e)
    sys.exit(1)


with open(filename, "r") as csvfile:
    dialect = csv.Sniffer().sniff(csvfile.readline(), [',',';'])
    csvfile.seek(0)
    reader = csv.DictReader(csvfile, delimiter = dialect.delimiter)
    for r in reader:
        location = r.get('location') # XPath des Elternelements
        field = location.split('/')[-1] # Feldname (actor, place etc) mit Namespace
        splitTag = mapping2[field].split(':') # Tag ohne Namespace
        tag = f"{{{NSMAP.get(splitTag[0])}}}{splitTag[1]}" #Tag in Clarke-Notation
        
        IDelements = tree.xpath(r.get('location') + "/" + mapping2[field], namespaces = NSMAP) # Liste aller ID-Elemente unter einem Eltern-Feld

        modifiedElements = dict() # Sammelt die Elemente

        # Geht durch CSV und erstellt etree.Element
        for k,v in r.items():
            m = re.match('^(\d+) (\S+)$', k)
            v = v.strip()
            if m: # Wenn Spaltenheader Index + Elementname
                if v != "":
                    index = int(m.group(1))
                    if not index in modifiedElements:
                        modifiedElements[index] = etree.Element(tag)
                    
                    if m.group(2) == "text":
                        modifiedElements[index].text = v
                    else:
                        modifiedElements[index].attrib[m.group(2)] = v

        # Elemente ersetzen
        for n, elem in enumerate(IDelements):
            if modifiedElements.get(n) is not None:
                IDelements[n].getparent().replace(IDelements[n],modifiedElements.pop(n))
            # Hier ließen sich durch ein else leere Felder aus der XML löschen

        # Überschüssige Elemente anhängen. ID-Felder sollen zu Beginn stehen
        for elem in modifiedElements.values():
            xpath = r.get('location') + "/" + mapping2[field] + "[last()]"
            last_elem = tree.xpath(xpath, namespaces = NSMAP)
            if last_elem:
                last_elem[0].addnext(elem)
            else:
                tree.xpath(r.get('location'), namespaces = NSMAP)[0].insert(0,elem)
                
outputfilename = xml_filename.stem + args.infix + xml_filename.suffix

outputString = etree.tostring(tree,
                        pretty_print=True,
                        xml_declaration=True,
                        encoding='UTF-8')

with open(outputfilename, "wb") as OUT:
    OUT.write(outputString)
    print(outputfilename, " written.")
