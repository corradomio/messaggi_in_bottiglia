import xml.etree.ElementTree as ET
from xmljson import badgerfish as bf
from json import dumps

tree = ET.parse("C:\\Users\MG\PycharmProjects\messaggi_in_bottiglia\questions\DomandeStudenti.xml")
root = tree.getroot()
# print(dumps(bf.data(root)))
iter = root.getiterator()

for element in iter:
    if element.tag == "question":
        print(dumps(bf.data(element)))
