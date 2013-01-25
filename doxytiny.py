# coding=UTF-8

from doxybase import *
import doxylayout

def linebreak (n):
	DocState.writer += "<br>"

def hruler (n):
	pass

def preformatted(n):
	DocState.writer += "<pre>"
	DocState.writer += n.text
	DocState.writer += "</pre>"

def programlisting(n):
	DocState.writer += "<code>"
	for line in n:
		''' \todo ID '''
		doxylayout.markup (line)
		DocState.writer += "<br>"

	DocState.writer += "</code>"

def verbatim (n):
	DocState.writer += n.text

def indexentry(n):
	pass

def orderedlist(n):
	DocState.writer += "<ol>"
	_doclist(n)
	DocState.writer += "</ol>"

def itemizedlist(n):
	DocState.writer += "<ul>"
	_doclist(n)
	DocState.writer += "</ul>"

def _doclist (n):
	#Guaranteed to only contain listitem nodes
	for child in n:
		assert child.tag == "listitem"

		DocState.writer += "<li>"
		doxylayout.markup (child)
		DocState.writer += "</li>"		


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
	DocState.writer += "<a href='" + n.get("url") + "'>"
	doxylayout.markup (n)
	DocState.writer += "</a>"

def bold (n):
	DocState.writer += "<b>"
	doxylayout.markup (n)
	DocState.writer += "</b>"

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
	doxylayout.markup (n)

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
	DocState.writer += "<p>"
	doxylayout.markup (n)
	DocState.writer += "</p>"

def sp (n):
	DocState.writer += " "



def highlight (n):
	doxylayout.markup (n)
