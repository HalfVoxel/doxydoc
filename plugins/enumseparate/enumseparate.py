from doxybase import Importer

def separate_enum_def():
	print ("Separating Enum Definitions")
	for xml in Importer.input_xml:
		for node in xml.findall(".//memberdef[@kind='enum']"):
			obj = node.get("docobj")
			if obj is None:
				print (node.get("id"))
			Importer.register_page(obj, node)


#Importer.add_event(2030, separate_enum_def)
