import xml.etree.ElementTree as ET

root = ET.parse("C:\\Users\MG\PycharmProjects\messaggi_in_bottiglia\questions\DomandeStudenti.xml")

#Create an iterator
iter = root.getiterator()

#Iterate
for element in iter:

    if element.tag == "question":
        #First the element tag name
        print("Element:", element.tag)

        #Next the child elements and text
        print("\tChildren:")

        for child in element.getchildren():
            #Child element tag name
            print("\t\tElement:", child.tag)

            if child.text:
                text = child.text
                # text = len(text) > 40 and text[:40] + "..." or text
                print("\t\tText:", repr(text))
