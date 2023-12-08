from lxml import etree
import argparse

parser = argparse.ArgumentParser(
                    prog='LIDOcombine - Combine multiple LIDO files into one',
                    description='Takes a list of LIDO XML files and combines them into one LIDO file.')

parser.add_argument("files", nargs="+")
parser.add_argument('-o', '--outfile', required = True)

args = parser.parse_args()
outputfilename = args.outfile


NSMAP = {"lido" : "http://www.lido-schema.org"}

LIDOWrap = etree.Element('{http://www.lido-schema.org}lidoWrap', nsmap = NSMAP)

for f in args.files:
    try:
        tree = etree.parse(f)
        NSMAP.update(tree.getroot().nsmap)
        LIDOWrap.extend(tree.xpath('//lido:lido', namespaces = NSMAP))
    except Exception as e:
        print(e)

etree.cleanup_namespaces(LIDOWrap) 
outputString = etree.tostring(LIDOWrap,
                        pretty_print=True,
                        xml_declaration=True,
                        encoding='UTF-8')

with open(outputfilename, "wb") as OUT:
    OUT.write(outputString)
    print(outputfilename, " written.")
