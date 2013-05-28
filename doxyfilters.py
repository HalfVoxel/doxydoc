import doxylayout
from doxybase import *

@jinjafilter
def markup(element):
	doxylayout.markup(element)
