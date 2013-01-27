import xml.etree.cElementTree as ET
from doxybase import *
import doxyext
import doxylayout
import re

def process_references (root):

    # for node in root.findall(".//*[@refid]"):
    #     try:
    #         # Doxygen can sometimes generate refid=""
    #         id = node.get("refid")
    #         obj = docobjs[id]
    #         node.set ("ref", obj)
    #     except KeyError:
    #         #print "Invalid refid: '" + node.get("refid") + "' in compound " + xml.find("compoundname").text
    #         #raise
    #         pass

    for node in root.iter():
        if node.get("refid") != None:
            try:
                # Doxygen can sometimes generate refid=""
                id = node.get("refid")
                obj = docobjs[id]
                node.set ("ref", obj)
            except KeyError:
                #print "Invalid refid: '" + node.get("refid") + "' in compound " + xml.find("compoundname").text
                #raise
                pass



    #for node in root.findall(".//*[@id]"):
    #    try:
    #        id = node.get("id")
    #        obj = docobjs[id]
    #        node.set ("docobj", obj)
    #    except KeyError:
    #        pass
        

def gather_compound_doc (xml):
    id = xml.get("id")
    compound = docobjs[id]

    DocState.compound = compound
    
    if compound.kind == "class" or compound.kind == "struct":
        gather_class_doc (xml)
    elif compound.kind == "page":
        gather_page_doc (xml)
    elif compound.kind == "namespace":
        gather_namespace_doc (xml)
    else:
        print ("Skipping " + compound.kind + " " + compound.name)
        return

def formatname (t):
    return t.replace ("::",".")

def gather_class_doc(xml):

    # xml
    # members
    # briefdesc
    # detaileddesc
    # protection
    # static
    # final
    # sealed
    # abstract
    # 
    # inherited
    # derived
    # 
    obj = xml.get("docobj")
    obj.protection = xml.get ("prot")
    obj.name = formatname (xml.find("compoundname").text)
    obj.members = []

    for member in xml.findall ("sectiondef/memberdef"):
        
        gather_member_doc (member)
        obj.members.append (member.get("docobj"))


    obj.briefdescription = xml.find("briefdescription")
    obj.detaileddescrption = xml.find("detaileddescrption")
    
    obj.final = xml.get("final") == "yes"
    obj.sealed = xml.get("sealed") == "yes"
    obj.abstract = xml.get("abstract") == "yes"

    obj.inherited = []
    for node in xml.findall("basecompoundref"):
        obj.inherited.append (node.get("ref"))

    obj.derived = []
    for node in xml.findall("derivedcompoundref"):
        obj.derived.append (node.get("ref"))


def gather_member_doc (member):

    # xml
    # id
    # name
    # kind
    # protection
    # virtual
    # static
    # override
    # readonly
    # reimplements
    # reimplementedby
    # briefdesc
    # detaileddesc
    # type
    m = member.get("docobj")
    assert m, "Invalid member " + str(member.get("id")) + " " + str(member.get("docobj"))
    

    m.xml = member
    #m.id should already be set
    m.name = formatname (member.find("name").text)
    m.kind = member.get("kind")

    prot = member.get("prot")
    if prot != None:
        m.protection = prot
    else:
        m.protection = None

    virt = member.get("virt")
    if virt != None and virt != "non-virtual":
        m.virtual = virt
    else:
        m.virtual = None

    m.static = member.get ("static") == "yes"

    m.reimplementedby = []
    for reimp in member.findall("reimplementedby"):
        obj = reimp.get("ref")
        m.reimplementedby.append(obj)

    m.reimplements = []
    for reimp in member.findall("reimplements"):
        obj = reimp.get("ref")
        m.reimplements.append (obj)
    
    override = len(m.reimplements) > 0 and m.virtual == "virtual"

    if override:
        assert member.find("type").text
        overrideType = member.find("type").text.split()[0]
        assert (overrideType != "override" and overrideType != "new", "Invalid override type: "+overrideType) 

        m.override = overrideType
    else:
        m.override = None

    m.briefdescription = member.find("briefdescription")
    m.detaileddescription = member.find("detaileddescription")

    m.type = member.find("type")

    m.readonly = False if m.type == None or m.type.text == None else m.type.text.startswith("readonly")
    
    if m.type != None and m.type.text != None:
        # Remove eventual 'override ' text at start of type.
        m.type.text = re.sub ("^(?:override|new|readonly)\s", "", m.type.text, 1)

def gather_page_doc (xml):

    # xml
    # id
    # name
    # kind
    # briefdesc
    # detaileddesc
    
    obj = xml.get("docobj")
    #id should already be set
    obj.name = formatname (xml.find("compoundname").text)
    obj.kind = xml.get("kind")
    obj.briefdescription = xml.find("briefdescription")
    obj.detaileddescription = xml.find("detaileddescription")

def gather_namespace_doc (xml):
    
    # xml
    # id
    # name
    # kind
    # briefdesc
    # detaileddesc
    #
    # innerclasses
    # innernamespaces
    # members
    
    obj = xml.get("docobj")
    #id should already be set
    obj.name = formatname (xml.find("compoundname").text)
    obj.kind = xml.get("kind")
    obj.briefdescription = xml.find("briefdescription")
    obj.detaileddescription = xml.find("detaileddescription")

    obj.innerclasses = []
    for node in xml.findall("innerclass"):
        obj.innerclasses.append (node.get("ref"))

    obj.innernamespaces = []
    for node in xml.findall("innernamespace"):
        obj.innernamespaces.append (node.get("ref"))

    obj.members = []

    for member in xml.findall ("sectiondef/memberdef"):
        
        gather_member_doc (member)
        obj.members.append (member.get("docobj"))



def generate_compound_doc (xml):

    compound = xml.get("docobj")
    
    DocState.pushwriter()
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
    f.write (DocState.popwriter())
    f.close()

    #generage_page_doc (compound)

def generate_class_doc (xml):
    id = xml.get("id")
    compound = docobjs[id]

    doxylayout.header ()

    doxylayout.pagetitle (compound.kind.title() + " " + compound.name)

    #doxylayout.compound_desc (compound)

    doxylayout.members (compound)

    doxylayout.footer ()

def generate_page_doc (xml):
    id = xml.get("id")
    compound = docobjs[id]

    doxylayout.header ()

    doxylayout.pagetitle (compound.name)

    doxylayout.description (compound.briefdescription)
    doxylayout.description (compound.detaileddescription)

    doxylayout.footer ()

def generate_namespace_doc (xml):
    id = xml.get("id")
    compound = docobjs[id]

    doxylayout.header ()

    doxylayout.pagetitle ("Namespace " + compound.name)

    doxylayout.description (compound.briefdescription)
    doxylayout.description (compound.detaileddescription)

    doxylayout.namespace_list_inner (compound)

    doxylayout.footer ()
