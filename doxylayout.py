from doxybase import *
import doxytiny

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
	DocState.writer += "<a href='%s' title='%s'>" % (obj.full_url(), tooltip)
	markup (refnode)
	DocState.writer += "</a>"

def linked_text (node):
	if len(node) == 0 and node.text != None:
		DocState.writer += node.text

	for n in node:

		if n.tag == "ref":
			ref (n)
		else:
			if n.text != None:
				DocState.writer += n.text

		if n.tail != None:
			DocState.writer += n.tail



def header ():
	DocState.writer += ("<html>"
	"<header>"
	"<link rel='stylesheet' type='text/css' href='style.css'>"
	"</header>"
	"<body>"
	"<div class='content'>")

def footer ():
	DocState.writer += ("</div>"
	"</body>"
	"</html>")

def pagetitle (title):
	DocState.writer += "\n<h1>" + title + "</h1>\n"

def member_section_heading (section):
	skind = section.get("kind")
	skind = skind.replace ("-"," ")
	skind = skind.replace ("attrib","attributes")
	skind = skind.replace ("func","functions")
	skind = skind.replace ("property","properties")
	skind = skind.title ()

	DocState.writer += "<h2>" + skind + "</h2>"

def members (xml):

	sections = xml.findall ("sectiondef")
	for section in sections:

		DocState.writer += "<div class ='member-sec'>"

		member_section_heading(section)

		members = section.findall ("memberdef")
		for m in members:
			member (m)

		DocState.writer += "</div>"


def member_heading (m):
	
	DocState.writer += prettify_prefix (m)


	type = m.find("type")
	if type != None:
		DocState.writer += " "
		#Write type
		linked_text(type)

	DocState.writer += " "
		
	name = m.find("name")
	DocState.writer += "<b>" + name.text + "</b>"

def desctitle (text):
	DocState.writer += "<h3>" + text + "</h3>"

def sect (sectnode, depth):
	''' sect* nodes '''

	title = sectnode.find("title")
	if title != None:
		DocState.writer += "<h" + str(depth) + " "
		id = sectnode.get(id)
		if id != None:
			DocState.writer += " id='get_anchor (id)' "

		DocState.writer += ">" + title.text + "</h" + str(depth) + ">"

	sectbase (sectnode)

def paragraph (paranode):
	''' para nodes '''

	DocState.writer += "<p>"
	markup (paranode)
	DocState.writer += "</p>"

def markup (node):
	''' Markup like nodes '''

	if len (node) == 0 and node.text != None:
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

def member_description (m):
	briefdesc = m.find("briefdescription")
	description (briefdesc)

	detdesc = m.find("detaileddescription")
	description (detdesc)
	

def member (m):

	DocState.writer += "<div class='memberdef'>"

	member_heading (m)

	member_description (m)

	DocState.writer += "</div>"

