from doxybase import *
import doxylayout

delimiter = "|$|"
rowdelimiter = "\n"
filename = "html/searchdata.csv"

def generate_index():

	f = file(filename, "w")

	for obj in Importer.iter_unique_docobjs():
		try:
			id = obj.full_url()
			name = obj.name
			desc = ""
			compound = ""
			kind = ""
			if hasattr(obj, "briefdescription"):
				Importer.pushwriterplain()
				doxylayout.description(obj.briefdescription)
				desc = Importer.popwriter()

			if hasattr(obj, "compound") and obj.compound is not None:
				compound = obj.compound.name

			if hasattr(obj, "kind") and obj.kind is not None:
				kind = obj.kind

			f.write(id + delimiter + name + delimiter + desc + delimiter + compound + delimiter + kind + rowdelimiter)
		except:
			print(vars(obj))
			raise

	f.close()

def searchbar():
	Importer.writer.element("li")
	Importer.writer.element("form", None, {"class": "navbar-search pull-right", "id": "searchform"})
	Importer.writer.element("input", None, {"type": "text", "class": "search-query", "id": "searchfield", "placeholder": "Search", "data-toggle": "dropdown", "autocomplete": "off"})
	Importer.writer.html("<ul class='dropdown-menu' role='menu' id='search-dropdown' aria-labelledby='dLabel'></ul>")
	Importer.writer.element("/form")
	Importer.writer.element("/li")

Importer.add_event(2600, generate_index)

Importer.trigger_listener("navheader", 100, searchbar)
