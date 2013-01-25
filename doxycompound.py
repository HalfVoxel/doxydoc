import xml.etree.cElementTree as ET
from doxybase import *
import doxyext
import doxylayout


def generate_compound_doc (xml):

    id = xml.get("id")
    compound = docobjs[id]
    
    DocState.writer.clear()
    DocState.compound = compound

    if compound.kind == "class" or compound.kind == "struct":
        generate_class_doc (xml)
    elif compound.kind == "page":
        generate_page_doc (xml)
    elif compound.kind == "namespace":
        generate_namespace_doc (xml)
    else:
        print ("Skipping " + compound.kind + " " + compound.name)
        return

    f = file(compound.full_path(), "w")
    f.write (str(DocState.writer))
    f.close()

    #generage_page_doc (compound)

def generate_class_doc (xml):
    id = xml.get("id")
    compound = docobjs[id]

    doxylayout.header ()

    doxylayout.pagetitle (compound.kind.title() + " " + compound.name)

    doxylayout.compound_desc (xml)

    doxylayout.members (xml)

    doxylayout.footer ()

def generate_page_doc (xml):
    id = xml.get("id")
    compound = docobjs[id]

    doxylayout.header ()

    doxylayout.pagetitle (compound.name)

    doxylayout.compound_desc (xml)

    doxylayout.footer ()

def generate_namespace_doc (xml):
    id = xml.get("id")
    compound = docobjs[id]

    doxylayout.header ()

    doxylayout.pagetitle ("Namespace " + compound.name)

    doxylayout.compound_desc (xml)

    doxylayout.namespace_list_inner (xml)

    doxylayout.footer ()
