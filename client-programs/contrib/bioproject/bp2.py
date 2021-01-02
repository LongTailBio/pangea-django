from Bio import Entrez
import xml.etree.ElementTree as ET
Entrez.email = "Your.Name.Here@example.org"


print('SEARCH')
handle = Entrez.esearch(db="sra", term="PRJNA545410")
record = Entrez.read(handle)
handle.close()
print(record)

print('FETCH')
# handle = Entrez.efetch(db="bioproject", id="545410")
# bioproj_xml = handle.read()
# root = ET.fromstring(bioproj_xml)

handle = Entrez.efetch(db='sra', id=record['IdList'][0])
xml_str = handle.read()
root = ET.fromstring(xml_str)

print(xml_str)
# print(root.tag)


def get_sra_files(root):
    sra_files = root.findall('SRAFiles')
    for child in root:
        sra_files += get_sra_files(child)
    return sra_files


def tree(root, d=0):
    print(' ' * d, root.tag, root.attrib)
    for child in root:
        tree(child, d=d + 1)

#print(tree(get_sra_files(root)[0]))
