import doxylayout
from doxybase import *

def markup(element):
	DocState.pushwriter()
	doxylayout.markup(element)
	return DocState.popwriter()

DocState.add_filter("markup", markup)
