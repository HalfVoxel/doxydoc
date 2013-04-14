from doxybase import *
import doxytiny

INITIAL_HEADING_DEPTH = 2

def try_call_tiny(name, arg):
	try:
		methodToCall = getattr(doxytiny, name)
	except AttributeError:
		return None, False

	result = methodToCall(arg)
	return result, True

def prettify_prefix(node):
	s = []
	prot = node.get("prot")
	if prot is not None:
		prot = prot.title()
		s.append(prot)

	virt = node.get("virt")
	if virt is not None and virt != "non-virtual":
		s.append(virt)

	override = node.find("reimplements") is not None and virt == "virtual"

	if override:
		assert node.find("type").text
		overrideType = node.find("type").text.split()[0]
		assert(overrideType != "override" and overrideType != "new", "Invalid override type: " + overrideType)

		s.append(overrideType)

	static = node.get("static")
	if static == "yes":
		s.append("static")

	# mutable?

	return " ".join(s)

def get_href(id):
	obj = DocState.get_docobj(id)
	return obj.full_url()

def get_anchor(id):
	obj = DocState.get_docobj(id)
	return obj.anchor

def refcompound(refnode):
	refid = refnode.get("refid")

	if refid == "":
		markup(refnode)
		return

	assert refid, refnode.tag + " was not a ref node. " + refnode.text + " " + str(refnode.attrib)

	#kind = refnode.get("kindref")
	#external = refnode.get("external")
	tooltip = refnode.get("tooltip")
	obj = DocState.get_docobj(id)

	obj = obj.compound
	assert obj

	DocState.depth_ref += 1
	if DocState.depth_ref > 1:
		DocState.writer += obj.name
	else:
		DocState.writer.element("a", obj.name, {"href": obj.full_url(), "rel": 'tooltip', "data-original-title": tooltip})
	DocState.depth_ref -= 1

def docobjref(obj):
	DocState.depth_ref += 1
	if DocState.depth_ref > 1:
		DocState.writer += obj.name
	else:
		if hasattr(obj, "briefdescription") and obj.briefdescription is not None:
			DocState.pushwriter()
			description(obj.briefdescription)
			tooltip = DocState.popwriter()
		else:
			tooltip = None

		DocState.writer.element("a", obj.name, {"href": obj.full_url(), "rel": 'tooltip', "data-original-title": tooltip})
	DocState.depth_ref -= 1

def ref(refnode):
	obj = refnode.get("ref")

	if obj is None:
		markup(refnode)
		return

	#assert refid, refnode.tag + " was not a ref node. " + refnode.text + " " + str(refnode.attrib)

	#kind = refnode.get("kindref")
	#external = refnode.get("external")
	#tooltip = refnode.get("tooltip")

	DocState.depth_ref += 1
	if DocState.depth_ref > 1:
		markup(refnode)
	else:

		if hasattr(obj, "briefdescription") and obj.briefdescription is not None:
			DocState.pushwriter()
			description(obj.briefdescription)
			tooltip = DocState.popwriter()
		else:
			tooltip = None

		DocState.writer.element("a", None, {"href": obj.full_url(), "rel": 'tooltip', "data-original-title": tooltip})
		markup(refnode)
		DocState.writer.element("/a")
	DocState.depth_ref -= 1

def ref_explicit(obj, text, tooltip=None):
	DocState.depth_ref += 1
	if DocState.depth_ref > 1:
		DocState.writer += text
	else:
		DocState.writer.element("a", text, {"href": obj.full_url(), "rel": 'tooltip', "data-original-title": tooltip})
	DocState.depth_ref -= 1

def match_external_ref(text):
	words = text.split()
	for i in range(0, len(words)):
		if i > 0:
			DocState.writer += " "
		try:
			obj = DocState.get_docobj("__external__" + words[i].strip())
			ref_explicit(obj, words[i], obj.tooltip if hasattr(obj, "tooltip") else None)
		except KeyError:
			DocState.writer += words[i]


def linked_text(node):
	if node.text is not None:
		match_external_ref(node.text)
		#DocState.writer += node.text

	for n in node:
		if n.tag == "ref":
			ref(n)
		else:
			if n.text is not None:
				match_external_ref(n.text)

		if n.tail is not None:
			match_external_ref(n.tail)
			#DocState.writer += n.tail

def header():
	DocState.writer.html(DocSettings.header)

def footer():
	DocState.writer.html(DocSettings.footer)

def begin_content():
	DocState.writer.html("<div class='content'>")

def end_content():
	DocState.writer.html("</div>")

def navheader():

	DocState.writer.html("<div class='navbar'><ul>")
	DocState.navitems.sort(key=lambda v: v.order)

	for item in DocState.navitems:
		DocState.writer.element("li")
		DocState.writer.element("a", item.label, {"href": item.ref.full_url()})
		DocState.writer.element("/li")

	DocState.writer.html("</div></ul>")

def pagetitle(title):
	DocState.writer.element("h1", title)

def member_section_heading(section):
	#skind = section.get("kind")
	#skind = skind.replace("-"," ")
	#skind = skind.replace("attrib","attributes")
	#skind = skind.replace("func","functions")
	#skind = skind.replace("property","properties")
	#skind = skind.title()

	DocState.writer.element("h2", section[0])

def get_member_sections(members):
	sections = []
	sections.append(("Public Variables", filter(lambda m: m.protection is "public" and m.kind is "variable", members)))
	sections.append(("All Members", members))
	return sections

def members_list(docobj):

	sections = get_member_sections(docobj.members)

	for section in sections:

		DocState.writer.element("h2", section[0])

		DocState.writer.element("table", None, {'class': 'table table-condensed table-striped member-list'})

		members = section[1]
		for m in members:
			DocState.writer.element("tr")

			# DocState.writer.element("td", None, {'class': 'member-prot'})
			# if m.protection is not None:
			# 	labelStyle = ""
			# 	if m.protection is "public":
			# 		labelStyle = "label-success"
			# 	elif m.protection is "private":
			# 		labelStyle = "label-inverse"
			# 	elif m.protection is "protected":
			# 		labelStyle = "label-warning"
			# 	elif m.protection is "package":
			# 		labelStyle = "label-info"

			# 	DocState.writer.element("span", m.protection.title(), {"class": "label " + labelStyle})

			# if m.readonly:
			# 	DocState.writer.element("span", "Readonly", {"class": "label label-warning"})
			# if m.static:
			# 	DocState.writer.element("span", "Static", {"class": "label label-info"})

			# DocState.writer.element("/td")

			# DocState.writer.element("td", None, {'class': 'member-type'})
			# type = m.type
			# if type is not None:

			# 	#Write type
			# 	linked_text(type)
			# DocState.writer.element("/td")

			DocState.writer.element("td", None, {'class': 'member-name'})
			ref_explicit(m, m.name)
			#DocState.writer += m.name
			DocState.writer.element("/td")

			DocState.writer.element("td", None, {'class': 'member-desc'})
			description(m.briefdescription)

			DocState.writer.element("/td")

			DocState.writer.element("/tr")

		DocState.writer.element("/table")

def members(docobj):

	sections = get_member_sections(docobj.members)

	for section in sections:

		DocState.writer.html("<div class ='member-sec'>")

		member_section_heading(section)

		members = section[1]
		for m in members:
			member(m)

		DocState.writer.html("</div>")


def member_heading(m):
	DocState.writer.element("h3")

	ls = []
	if m.protection is not None:
		ls.append(m.protection.title())
	if m.readonly:
		ls.append("readonly")

	if m.static:
		ls.append("static")

	DocState.writer += ' '.join(ls)

	type = m.type
	if type is not None:
		if len(ls) > 0:
			DocState.writer.element("span", None, {"class": 'member-type'})

		#Write type
		linked_text(type)

	DocState.writer.element("/span")
	DocState.writer.element("span", None, {"class": 'member-name'})

	name = m.name
	DocState.writer += name

	DocState.writer.element("/span")

	if m.params is not None:
		DocState.writer += " "

		DocState.writer.element("span", None, {"class": "member-params"})
		DocState.writer += "("
		for i, param in enumerate(m.params):
			DocState.writer += " "
			markup(param.type)

			DocState.writer += " "

			if param.description is not None:
				DocState.pushwriter()
				description(param.description)
				tooltip = DocState.popwriter()
				DocState.writer.element("span", None, {"data-original-title": tooltip})
				DocState.writer += param.name
				DocState.writer.element("/span")
			else:
				DocState.writer += param.name

			if i < len(m.params) - 1:
				DocState.writer += ","

		DocState.writer.element("/span")

	DocState.writer.element("/h3")

def desctitle(text):
	DocState.writer.element("h3", text)

def sect(sectnode, depth):
	''' sect* nodes '''

	title = sectnode.find("title")
	if title is not None:
		DocState.writer.element("h" + str(depth + INITIAL_HEADING_DEPTH), title.text, {"id": get_anchor(sectnode.get("id"))})

	sectbase(sectnode)

def paragraph(paranode):
	''' para nodes '''

	DocState.writer.elem("p")
	markup(paranode)
	DocState.writer.elem("/p")

def markup(node):
	''' Markup like nodes '''

	if node.text is not None:
		DocState.writer += node.text

	for n in node:
		result, ok = try_call_tiny(n.tag, n)
		if not ok:
			print("Not handled: " + n.tag)
			if n.text is not None:
				DocState.writer += n.text

		if n.tail is not None:
			DocState.writer += n.tail

def internal(internalnode):
	''' internal nodes '''

	print("Skipping internal data")

def sectbase(node):
	for n in node:
		if n == node:
			continue

		if n.tag is "para":
			paragraph(n)
		elif n.tag is "sect1":
			sect(n, 1)
		elif n.tag is "sect2":
			sect(n, 2)
		elif n.tag is "sect3":
			sect(n, 3)
		elif n.tag is "sect4":
			sect(n, 4)
		elif n.tag is "sect5":
			sect(n, 5)
		elif n.tag is "simplesectsep":
			doxytiny.simplesectsep(n)
		elif n.tag is "title":
			#A sect should have been the parent, so it should have been handled
			pass
		elif n.tag == "internal":
			internal(n)
		else:
			print("Not handled: " + n.tag)

def description(descnode):
	if descnode is not None:
		title = descnode.find("title")
		if title is not None:
			desctitle(title.text)

		sectbase(descnode)

def member_reimplements(m):
	reimps = m.findall("reimplementedby")
	for reimp in reimps:
		#obj = reimp.get("ref")
		DocState.writer.html("<span>Reimplemented in ")
		refcompound(reimp)
		DocState.writer.hmtl("</span>")

	reimps = m.findall("reimplements")
	for reimp in reimps:
		#obj = reimp.get("ref")
		DocState.writer.html("<span>Overrides implementation in ")
		refcompound(reimp)
		DocState.writer.html("</span>")

def member(m):

	DocState.writer.element("div", None, {"class": 'memberdef', "id": m.anchor})

	member_heading(m)

	description(m.briefdescription)
	description(m.detaileddescription)

	DocState.writer.element("/div")

def compound_desc(compxml):

	briefdesc = compxml.find("briefdescription")
	detdesc = compxml.find("detaileddescription")

	description(briefdesc)
	description(detdesc)

def page_list_inner(obj):

	pages = []
	if obj is None:
		for k, obj2 in DocState._docobjs.iteritems():
			if obj2.kind == "page" and(not hasattr(obj2, "parentpage") or obj2.parentpage is None) and not obj2 in pages:
				pages.append(obj2)
	else:
		pages = obj.subpages

	if pages is None or len(pages) == 0:
		return

	DocState.writer.element("ul")

	for p in pages:
		DocState.writer.element("li")
		print("Depth: " + str(DocState.depth_ref))
		docobjref(p)
		page_list_inner(p)
		DocState.writer.element("/li")

	DocState.writer.element("/ul")

def namespace_list_inner(obj):

	DocState.writer.element("table", None, {"class": "compound-view"})

	namespaces = []
	gridobjs = []
	if hasattr(obj, "innerclasses"):
		for obj2 in obj.innerclasses:
			if(obj2.kind == "class" or obj2.kind == "struct") and not obj2 in gridobjs:
				gridobjs.append(obj2)
	else:
		for k, obj2 in DocState._docobjs.iteritems():
			if(obj2.kind == "class" or obj2.kind == "struct") and not obj2 in gridobjs:
				gridobjs.append(obj2)

	if hasattr(obj, "innernamespaces"):
		for ns in obj.innernamespaces:
			namespaces.append(ns)
	else:
		for k, obj2 in DocState._docobjs.iteritems():
			if obj2.kind == "namespace" and not obj2 in namespaces:
				if hasattr(obj2, "innerclasses") and len(obj2.innerclasses) > 0:
					namespaces.append(obj2)

	# Apparently, this manages to sort them by name.
	# Even without me specifying what to sort by.
	# Python...
	gridobjs.sort()
	namespaces.sort()

	# Number of columns
	xwidth = 4
	ns_colspan = int(xwidth / 2)

	counter = 0

	for obj2 in namespaces:
		if counter % xwidth is 0:
			if counter > 0:
				DocState.writer.element("/tr")
			DocState.writer.element("tr")

		DocState.writer.element("td", None, {"colspan": str(ns_colspan)})
		DocState.depth_ref += 1
		DocState.writer.element("a", None, {"href": obj2.full_url()})
		DocState.writer.element("b", obj2.name)

		#doxylayout.docobjref(obj2)
		#DocState.writer.element("p")
		description(obj2.briefdescription)
		#DocState.writer.element("/p")
		DocState.writer.element("/a")
		DocState.writer.element("/td")

		counter += ns_colspan

		DocState.depth_ref -= 1

	if(len(namespaces) > 0):
		DocState.writer.element("/tr")

	counter = 0

	for obj2 in gridobjs:
		# NOTE: Add enum
		if counter % xwidth == 0:
			if counter > 0:
				DocState.writer.element("/tr")
			DocState.writer.element("tr")

		DocState.writer.element("td")

		DocState.depth_ref += 1
		DocState.writer.element("a", None, {"href": obj2.full_url()})
		DocState.writer.element("b", obj2.name)

		#doxylayout.docobjref(obj2)
		#DocState.writer.element("p")
		description(obj2.briefdescription)
		#DocState.writer.element("/p")
		DocState.writer.element("/a")
		DocState.writer.element("/td")
		DocState.depth_ref -= 1

		counter += 1

	DocState.writer.element("/tr")
	DocState.writer.element("/table")

def namespace_inner_class(obj):
	DocState.writer.elem("li")

	docobjref(obj)

	DocState.writer.elem("/li")
