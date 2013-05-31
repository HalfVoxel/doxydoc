from doxybase import DocState

def separate_enum_def():
	print ("Separating Enum Definitions")
	for xml in DocState.input_xml:
		for node in xml.findall(".//memberdef[@kind='enum']"):
			obj = node.get("docobj")
			if obj is None:
				print (node.get("id"))
			DocState.register_page(obj, node)


#DocState.add_event(2030, separate_enum_def)
