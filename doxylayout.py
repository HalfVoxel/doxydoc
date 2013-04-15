from doxybase import *
import doxytiny
from doxysettings import DocSettings

INITIAL_HEADING_DEPTH = 2

def try_call_tiny(name, arg):
	try:
		methodToCall = getattr(doxytiny, name)
	except AttributeError:
		return None, False

	result = methodToCall(arg)
	return result, True

def is_hidden(docobj):
	if docobj.hidden:
		return True
	return False

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
		assert overrideType != "override" and overrideType != "new", "Invalid override type: " + overrideType

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


	# Prevent recursive loops of links in the tooltips
	DocState.depth_ref += 1
	if DocState.depth_ref > 1 or is_hidden(obj):
		DocState.writer += obj.name
	else:
		# Write out anchor element
		DocState.writer.element("a", obj.name, {"href": obj.full_url(), "rel": 'tooltip', "data-original-title": tooltip})
	DocState.depth_ref -= 1

def docobjref(obj):
	# Prevent recursive loops of links in the tooltips
	DocState.depth_ref += 1
	if DocState.depth_ref > 1 or is_hidden(obj):
		DocState.writer += obj.name
	else:
		if hasattr(obj, "briefdescription") and obj.briefdescription is not None:
			DocState.pushwriter()
			description(obj.briefdescription)
			tooltip = DocState.popwriter()
		else:
			tooltip = None

		# Write out anchor element
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
	if DocState.depth_ref > 1 or is_hidden(obj):
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
	if DocState.depth_ref > 1 or is_hidden(obj):
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

def file_path(path):
	if path is None:
		return

	DocState.writer.element("span", path, {"class": "file-location"})

def member_section_heading(section):
	#skind = section.get("kind")
	#skind = skind.replace("-"," ")
	#skind = skind.replace("attrib","attributes")
	#skind = skind.replace("func","functions")
	#skind = skind.replace("property","properties")
	#skind = skind.title()

	DocState.writer.element("h2", section[0])

''' Returns a list of sections in which to group members for display '''
def get_member_sections(compound, members):
	sections = []

	sections.append(("Public Variables", filter(lambda m: m.protection == "public" and m.kind == "variable" and not m.static and m.compound == compound, members)))
	sections.append(("Public Methods", filter(lambda m: m.protection == "public" and m.kind == "function" and not m.static and m.compound == compound, members)))
	sections.append(("Public Static Variables", filter(lambda m: m.protection == "public" and m.kind == "variable" and m.static and m.compound == compound, members)))
	sections.append(("Public Static Methods", filter(lambda m: m.protection == "public" and m.kind == "function" and m.static and m.compound == compound, members)))
	sections.append(("Private Members", filter(lambda m: m.protection != "public" and m.compound == compound, members)))
	
	# Handling it specially, it's no point explicitly showing an empty section when a class does no inherit any members
	ls = filter(lambda m: m.compound != compound, members)
	if len(ls) > 0:
		sections.append(("Inherited Members", ls))
	
	#sections.append(("All Members", members))
	return sections

''' Shows the protection of a member in the table/list view '''
def member_list_protection(member):

	DocState.writer.element("span", member.protection.title())

	if member.readonly:
		DocState.writer.element("span", "Readonly")
	if member.static:
		DocState.writer.element("span", "Static")

''' Displays the member's type. Used in the members table '''
def member_list_type(member):
	if member.type is not None:
		# Write type
		linked_text(member.type)
	

def members_list(docobj):

	DocState.writer.element("div", None, {"class": "member-list"})

	sections = get_member_sections(docobj, docobj.all_members)

	for section in sections:

		members = section[1]

		if len(members) == 0:
			continue

		DocState.writer.element("h2", section[0])

		DocState.writer.element("table", None, {'class': 'table table-condensed table-striped member-list-section'})

		for m in members:
			DocState.writer.element("tr")

			# Show protection in table if requested
			if DocSettings.show_member_protection_in_list:
				DocState.writer.element("td", None, {'class': 'member-prot'})
				member_list_protection(m)
				DocState.writer.element("/td")
			
			# Show type in table if requested
			if DocSettings.show_member_protection_in_list:
				DocState.writer.element("td", None, {'class': 'member-type'})
				member_list_type(m)
				DocState.writer.element("/td")

			DocState.writer.element("td", None, {'class': 'member-name'})
			ref_explicit(m, m.name)
			#DocState.writer += m.name
			DocState.writer.element("/td")

			DocState.writer.element("td", None, {'class': 'member-desc'})
			description(m.briefdescription)

			DocState.writer.element("/td")

			DocState.writer.element("/tr")

		DocState.writer.element("/table")

	DocState.writer.element("/div")

def members_section_empty_message(section):
	DocState.writer.element("p", "Seems there are no members to be listed here", {"class": "empty-section"})

def members(docobj):

	sections = get_member_sections(docobj, docobj.members)

	for section in sections:

		members = section[1]

		if not DocSettings.keep_empty_member_sections:
			if sum(not is_hidden(m) for m in members) == 0:
				continue

		DocState.writer.html("<div class ='member-sec'>")

		member_section_heading(section)

		count = 0
		members = section[1]
		for m in members:
			# Ignore hidden members
			if not is_hidden(m):
				member(m)
				count += 1

		if count == 0:
			members_section_empty_message(section)

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
	
	#These kinds of members have a () list
	if m.kind == "function":
		if len(ls) > 0:
			DocState.writer.element("span", None, {"class": 'member-type'})

		#Write type
		linked_text(m.type)

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
			linked_text(param.type)

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
			print("[W1] Not handled: " + n.tag)
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


		if n.tag == "para":
			paragraph(n)
		elif n.tag == "sect1":
			sect(n, 1)
		elif n.tag == "sect2":
			sect(n, 2)
		elif n.tag == "sect3":
			sect(n, 3)
		elif n.tag == "sect4":
			sect(n, 4)
		elif n.tag == "sect5":
			sect(n, 5)
		elif n.tag == "simplesectsep":
			doxytiny.simplesectsep(n)
		elif n.tag == "title":
			#A sect should have been the parent, so it should have been handled
			pass
		elif n.tag == "internal":
			internal(n)
		else:
			print("[W2] Not handled: " + n.tag)

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
		docobjref(p)
		page_list_inner(p)
		DocState.writer.element("/li")

	DocState.writer.element("/ul")

def group_list_inner_classes(objs):
	DocState.writer.element("table", None, {"class": "inner-class-list table table-condensed table-striped"})
	for n in objs:
		DocState.writer.element("tr")
		DocState.writer.element("td", lambda: docobjref(n))
		DocState.writer.element("td", lambda: description(n.briefdescription))
		DocState.writer.element("/tr")

	DocState.writer.element("/table")

def group_list_inner_namespaces(objs):
	group_list_inner_classes(objs)

def group_list_inner_groups(objs):
	group_list_inner_classes(objs)

''' Show a list of classes a file contains.
	\param obj A list of DocObj
'''
def file_list_inner_classes(obj):
	''' \bug Either class, struct or interface '''
	DocState.writer.element("h4", "This file defines the following class" + ("es" if len(obj) > 1 else "") + ":")
	DocState.writer.element("ul", None, {"class": "inner-class-list"})
	for n in obj:
		DocState.writer.element("li", lambda: docobjref(n))

	DocState.writer.element("/ul")

def file_list_inner_namespaces(obj):
	pass

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
