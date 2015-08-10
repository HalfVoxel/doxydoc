import doxylayout
from doxybase import JinjaFilter


@JinjaFilter
def markup(element):
    return doxylayout.markup(element)
