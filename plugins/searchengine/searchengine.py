from doxybase import *
import doxylayout

delimiter = "|$|"
rowdelimiter = "\n"
filename = "html/searchdata.csv"

def generate_index():

	f = file(filename, "w")

	for obj in DocState.iter_unique_docobjs():
		try:
			id = obj.full_url()
			name = obj.name
			desc = ""
			compound = ""
			kind = ""
			if hasattr(obj, "briefdescription"):
				DocState.pushwriterplain()
				doxylayout.description(obj.briefdescription)
				desc = DocState.popwriter()

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
	DocState.writer.element("li")
	DocState.writer.element("form", None, {"class": "navbar-search pull-right", "id": "searchform"})
	DocState.writer.element("input", None, {"type": "text", "class": "search-query", "id": "searchfield", "placeholder": "Search", "data-toggle": "dropdown", "autocomplete": "off"})
	DocState.writer.html("<ul class='dropdown-menu' role='menu' id='search-dropdown' aria-labelledby='dLabel'></ul>")
	DocState.writer.element("/form")
	DocState.writer.element("/li")

DocState.add_event(2600, generate_index)

DocState.trigger_listener("navheader", 100, searchbar)
