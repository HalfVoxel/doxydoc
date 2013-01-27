from doxybase import *
import doxytiny
import re

def try_call_tiny (name, arg):
    try:
        methodToCall = getattr(doxytiny, name)
    except AttributeError:
        return None, False

    result = methodToCall(arg)
    return result, True

def prettify_prefix (node):
	s = []
	prot = node.get("prot")
	if prot != None:
		prot = prot.title ()
		s.append(prot)
	
	virt = node.get("virt")
	if virt != None and virt != "non-virtual":
		s.append (virt)

	override = node.find("reimplements") != None and virt == "virtual"

	if override:
		assert node.find("type").text
		overrideType = node.find("type").text.split()[0]
		assert (overrideType != "override" and overrideType != "new", "Invalid override type: "+overrideType) 

		s.append(overrideType)

	static = node.get ("static")
	if static == "yes":
		s.append ("static")

	# mutable?
	
	return " ".join(s)

def get_href (id):
	obj = docobjs[id]
	return obj.full_url()

def get_anchor (id):
	obj = docobjs[id]
	return obj.anchor

def refcompound (refnode):
	refid = refnode.get("refid")

	if refid == "":
		markup (refnode)
		return

	assert refid, refnode.tag + " was not a ref node. " + refnode.text + " " + str(refnode.attrib)

	kind = refnode.get("kindref")
	external = refnode.get("external")
	tooltip = refnode.get("tooltip")
	obj = docobjs[refid]

	obj = obj.compound
	assert obj

	DocState.depth_ref += 1
	if DocState.depth_ref > 1:
		DocState.writer += obj.name
	else:
		DocState.writer.element("a", obj.name, {"href": obj.full_url(), "rel": 'tooltip', "data-original-title": tooltip})
	DocState.depth_ref -= 1

def docobjref (obj):
	DocState.depth_ref += 1
	if DocState.depth_ref > 1:
		DocState.writer += obj.name
	else:
		if hasattr(obj,"briefdescription") and obj.briefdescription != None:
			DocState.pushwriter()
			description(obj.briefdescription)
			tooltip = DocState.popwriter()
		else:
			tooltip = None

		DocState.writer.element("a", obj.name, {"href": obj.full_url(), "rel": 'tooltip', "data-original-title": tooltip})
	DocState.depth_ref -= 1

def ref (refnode):
	refid = refnode.get("refid")

	if refid == "":
		markup (refnode)
		return

	assert refid, refnode.tag + " was not a ref node. " + refnode.text + " " + str(refnode.attrib)

	kind = refnode.get("kindref")
	external = refnode.get("external")
	tooltip = refnode.get("tooltip")
	obj = docobjs[refid]

	DocState.depth_ref += 1
	if DocState.depth_ref > 1:
		markup (refnode)
	else:
		DocState.writer.element("a", None, {"href": obj.full_url(), "rel": 'tooltip', "data-original-title": tooltip})
		markup (refnode)
		DocState.writer.element("/a")
	DocState.depth_ref -= 1

def ref_explicit (obj, text, tooltip = None):
	DocState.depth_ref += 1
	if DocState.depth_ref > 1:
		DocState.writer += text
	else:
		DocState.writer.element("a", text, {"href": obj.full_url(), "rel": 'tooltip', "data-original-title": tooltip})
	DocState.depth_ref -= 1

def match_external_ref (text):
	words = text.split ()
	for i in range(0,len(words)):
		if i > 0:
			DocState.writer += " "
		try:
			obj = docobjs["__external__" + words[i].strip()]
			ref_explicit (obj, words[i], obj.tooltip if hasattr (obj,"tooltip") else None)
		except KeyError:
			DocState.writer += words[i]


def linked_text (node):
	if node.text != None:
		match_external_ref (node.text)
		#DocState.writer += node.text

	for n in node:
		if n.tag == "ref":
			ref (n)
		else:
			if n.text != None:
				match_external_ref (n.text)

		if n.tail != None:
			match_external_ref (n.tail)
			#DocState.writer += n.tail



def header ():
	DocState.writer.html(DocSettings.header)

def footer ():
	DocState.writer.html(DocSettings.footer)

def pagetitle (title):
	DocState.writer.element ("h1", title)

def member_section_heading (section):
	#skind = section.get("kind")
	#skind = skind.replace ("-"," ")
	#skind = skind.replace ("attrib","attributes")
	#skind = skind.replace ("func","functions")
	#skind = skind.replace ("property","properties")
	#skind = skind.title ()

	DocState.writer.element ("h2", section[0])

def members (docobj):

	members = docobj.members

	sections = []
	sections.append (("Public Variables", filter (lambda m: m.protection == "public" and m.kind == "variable", members)))
	sections.append (("All Members", members))

	for section in sections:

		DocState.writer.html ("<div class ='member-sec'>")

		member_section_heading(section)

		members = section[1]
		for m in members:
			member (m)

		DocState.writer.html ("</div>")


def member_heading (m):
	#Note, slightly unsafe, could possibly break html
	DocState.writer.html("<h3 id=%s>" % (m.anchor))

	type = m.type
	if type != None:

		#Write type
		linked_text(type)

	DocState.writer += " "
		
	name = m.name
	#DocState.writer.element ("b",name)
	DocState.writer += name

	DocState.writer.html("</h3>")

	if m.protection != None:
		labelStyle = ""
		if m.protection == "public":
			labelStyle = "label-success"
		elif m.protection == "private":
			labelStyle = "label-inverse"
		elif m.protection == "protected":
			labelStyle = "label-warning"
		elif m.protection == "package":
			labelStyle = "label-info"

		DocState.writer.element ("span", m.protection.title(), {"class": "label " + labelStyle})

	if m.readonly:
		DocState.writer.element ("span", "Readonly", {"class": "label label-warning"})
	if m.static:
		DocState.writer.element ("span", "Static", {"class": "label label-info"})
		

def desctitle (text):
	DocState.writer.element ("h3", text)

def sect (sectnode, depth):
	''' sect* nodes '''

	title = sectnode.find("title")
	if title != None:
		DocState.writer.html("<h" + str(depth) + " ")
		id = sectnode.get("id")
		if id != None:
			#note slightly unsafe, might break html
			DocState.writer.html(" id='" + get_anchor (id) + "' ")

		DocState.writer.html (">")
		DocState.writer += title.text
		DocState.writer.html ("</h" + str(depth) + ">")

	sectbase (sectnode)

def paragraph (paranode):
	''' para nodes '''

	DocState.writer.elem("p")
	markup (paranode)
	DocState.writer.elem ("/p")

def markup (node):
	''' Markup like nodes '''

	if node.text != None:
		DocState.writer += node.text

	for n in node:
		result, ok = try_call_tiny (n.tag, n)
		if not ok:
			print ("Not handled: " + n.tag)
			if n.text != None:
				DocState.writer += n.text

		if n.tail != None:
			DocState.writer += n.tail

def internal (internalnode):
	''' internal nodes '''

	print ("Skipping internal data")

def sectbase (node):
	for n in node:
		if n == node:
			continue

		if n.tag == "para":
			paragraph (n)
		elif n.tag == "sect1":
			sect (n,1)
		elif n.tag == "sect2":
			sect (n,2)
		elif n.tag == "sect3":
			sect (n,3)
		elif n.tag == "sect4":
			sect (n,4)
		elif n.tag == "sect5":
			sect (n,5)
		elif n.tag == "title":
			#A sect should have been the parent, so it should have been handled
			pass
		elif n.tag == "internal":
			internal (n)
		else:
			print ("Not handled: " + n.tag)

def description (descnode):
	if descnode != None:
		title = descnode.find("title")
		if title != None:
			desctitle (title.text)

		sectbase (descnode)

def member_reimplements (m):
	reimps = m.findall("reimplementedby")
	for reimp in reimps:
		obj = docobjs[reimp.get("refid")]
		DocState.writer.html("<span>Reimplemented in ")
		refcompound (reimp)
		DocState.writer.hmtl ("</span>")

	reimps = m.findall("reimplements")
	for reimp in reimps:
		obj = docobjs[reimp.get("refid")]
		DocState.writer.html ("<span>Overrides implementation in ")
		refcompound (reimp)
		DocState.writer.html ("</span>")

def member (m):

	DocState.writer.html ("<div class='memberdef'>")

	member_heading (m)

	description (m.briefdescription)
	description (m.detaileddescription)

	DocState.writer.html ("</div>")

def compound_desc (compxml):

	briefdesc = compxml.find ("briefdescription")
	detdesc = compxml.find ("detaileddescription")

	description(briefdesc)
	description(detdesc)

def namespace_list_inner (compound):

	DocState.writer.elem ("ul")
	for obj in compound.innerclasses:
		namespace_inner_class (obj)
	DocState.writer.elem ("/ul")

def namespace_inner_class (obj):
	DocState.writer.elem ("li")

	docobjref (obj)

	DocState.writer.elem ("/li")
