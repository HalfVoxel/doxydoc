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
	pass

def itermizedlist(n):
	pass

def simplesect(n):
	pass

def title(n):
	pass

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

def bold (n):
	DocState.writer += "<b>"
	doxylayout.markup (n)
	DocState.writer += "</b>"

def sp (n):
	DocState.writer += " "

def ref (n):
	doxylayout.ref (n)

def highlight (n):
	doxylayout.markup (n)
