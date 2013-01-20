import xml.etree.cElementTree as ET
from doxybase import *
import doxyext
import doxylayout


def generate_compound_doc (xml):

    id = xml.get("id")
    compound = docobjs[id]

    if compound.kind == "class":
        generate_class_doc (xml)
    elif compound.kind == "page":
        print ("Skipping page " + compound.name)
    #generage_page_doc (compound)

def generate_class_doc (xml):
    id = xml.get("id")
    compound = docobjs[id]

    DocState.writer = StringBuilder ()
    DocState.compound = compound

    doxylayout.header ()

    doxylayout.pagetitle (compound.name)

    doxylayout.members (xml)

    doxylayout.footer ()

    f = file(compound.full_path(), "w")
    f.write (str(DocState.writer))
    f.close()


