# coding=UTF-8

from doxybase import *
import doxylayout

def linebreak (n):
	DocState.writer.elem("br")

def hruler (n):
	pass

def preformatted(n):
	DocState.writer.elem("pre")
	DocState.writer += n.text
	DocState.writer.elem("/pre")

def programlisting(n):
	DocState.writer.elem("code")
	for line in n:
		''' \todo ID '''
		doxylayout.markup (line)
		DocState.writer.elem("br")

	DocState.writer.elem("/code")

def verbatim (n):
	DocState.writer.html(n.text)

def indexentry(n):
	pass

def orderedlist(n):
	DocState.writer.elem("ol")
	_doclist(n)
	DocState.writer.elem("/ol")

def itemizedlist(n):
	DocState.writer.elem("ul")
	_doclist(n)
	DocState.writer.elem("/ul")

def _doclist (n):
	#Guaranteed to only contain listitem nodes
	for child in n:
		assert child.tag == "listitem"

		DocState.writer.elem("li")
		doxylayout.markup (child)
		DocState.writer.elem("/li")		


def simplesect(n):
	pass

def title(n):
	raise false, "Title tags should have been handled"

def variablelist(n):
	pass

def table(n):
	pass

def heading(n):
	pass

def image(n):
	pass

def dotfile(n):
	pass

def toclist(n):
	pass

def xrefsect(n):
	pass

def copydoc(n):
	pass

def blockquote(n):
	pass

##########################
#### docTitleCmdGroup ####
##########################

def ulink(n):
	DocState.writer.elem("a href='" + n.get("url") + "'")
	doxylayout.markup (n)
	DocState.writer.elem("/a")

def bold (n):
	DocState.writer.elem("b")
	doxylayout.markup (n)
	DocState.writer.elem("/b")

def emphasis (n):
	bold(n)

def computeroutput(n):
	preformatted (n)

def subscript(n):
	pass

def superscript(n):
	pass

def center(n):
	pass

def small(n):
	pass

def htmlonly (n):
	verbatim (n)

## These should be pass only functions actually

def manonly (n):
	pass

def xmlonly (n):
	pass
	
def rtfonly (n):
	pass
	
def latexonly (n):
	pass

##May look similar to mdash in a monospace font, but it is not
def ndash (n):
	DocState.writer += "–"

def mdash (n):
	DocState.writer += "—"

###...


def ref (n):
	doxylayout.ref (n)

##########################
#### docTitleCmdGroup ####
##########################

def para (n):
	DocState.writer.elem("p")
	doxylayout.markup (n)
	DocState.writer.elem("/p")

def sp (n):
	DocState.writer += " "



def highlight (n):
	doxylayout.markup (n)
