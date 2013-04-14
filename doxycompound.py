from doxybase import *
#import doxyext
import doxylayout
import re

def process_references_root(root):

    # for node in root.findall(".//*[@refid]"):
    #     try:
    #         # Doxygen can sometimes generate refid=""
    #         id = node.get("refid")
    #         obj = docobjs[id]
    #         node.set("ref", obj)
    #     except KeyError:
    #         #print "Invalid refid: '" + node.get("refid") + "' in compound " + xml.find("compoundname").text
    #         #raise
    #         pass

    for node in root.iter():
        if node.get("refid") is not None:
            try:
                # Doxygen can sometimes generate refid=""
                id = node.get("refid")
                obj = DocState.get_docobj(id)
                node.set("ref", obj)
            except KeyError:
                #print "Invalid refid: '" + node.get("refid") + "' in compound " + xml.find("compoundname").text
                #raise
                pass

    #for node in root.findall(".//*[@id]"):
    #    try:
    #        id = node.get("id")
    #        obj = docobjs[id]
    #        node.set("docobj", obj)
    #    except KeyError:
    #        pass
        
def pre_output():
    pass

def gather_compound_doc(xml):
    #id = xml.get("id")
    compound = xml.get("docobj")

    DocState.compound = compound
    
    if compound.kind is "class" or compound.kind is "struct":
        gather_class_doc(xml)
    elif compound.kind is "page":
        gather_page_doc(xml)
    elif compound.kind is "namespace":
        gather_namespace_doc(xml)
    else:
        print("Skipping " + compound.kind + " " + compound.name)
        return

def formatname(t):
    return t.replace("::", ".")

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
    obj.protection = xml.get("prot")
    obj.name = formatname(xml.find("compoundname").text)
    obj.members = []

    for member in xml.findall("sectiondef/memberdef"):
        
        gather_member_doc(member)
        obj.members.append(member.get("docobj"))

    obj.briefdescription = xml.find("briefdescription")
    obj.detaileddescription = xml.find("detaileddescription")
    
    obj.final = xml.get("final") is "yes"
    obj.sealed = xml.get("sealed") is "yes"
    obj.abstract = xml.get("abstract") is "yes"

    obj.inherited = []
    for node in xml.findall("basecompoundref"):
        obj.inherited.append(node.get("ref"))

    obj.derived = []
    for node in xml.findall("derivedcompoundref"):
        obj.derived.append(node.get("ref"))


def gather_member_doc(member):

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
    m.name = formatname(member.find("name").text)
    m.kind = member.get("kind")

    prot = member.get("prot")
    if prot is not None:
        m.protection = prot
    else:
        m.protection = None

    virt = member.get("virt")
    if virt is not None and virt is not "non-virtual":
        m.virtual = virt
    else:
        m.virtual = None

    m.static = member.get("static") is "yes"

    m.reimplementedby = []
    for reimp in member.findall("reimplementedby"):
        obj = reimp.get("ref")
        m.reimplementedby.append(obj)

    m.reimplements = []
    for reimp in member.findall("reimplements"):
        obj = reimp.get("ref")
        m.reimplements.append(obj)
    
    override = len(m.reimplements) > 0 and m.virtual is "virtual"

    if override:
        assert member.find("type").text
        overrideType = member.find("type").text.split()[0]
        override = overrideType is "override" or overrideType is "new"

        # For abstract classes or interfaces, it might reimplement some function without overriding it
        # thus the need to check again here
        if override:
            m.override = overrideType
        else:
            m.override = None
    else:
        m.override = None

    # Find descriptions
    m.briefdescription = member.find("briefdescription")
    m.detaileddescription = member.find("detaileddescription")

    # Find type
    m.type = member.find("type")

    # Is the member read only. Doxygen will put 'readonly' at the start of the 'type' field if it is readonly
    m.readonly = False if m.type is None or m.type.text is None else m.type.text.startswith("readonly")
    
    if m.type is not None and m.type.text is not None:
        # Remove eventual 'override ' text at start of type.
        m.type.text = re.sub("^(?:override|new|readonly)\s", "", m.type.text, 1)


    # Parse(function) arguments
    argsstring = member.find("argsstring")
    # Test if this member has arguments(.text will be None if the tag is empty)
    if argsstring is not None and argsstring.text is not None:
        m.argsstring = argsstring.text

        params = member.findall("param")
        m.params = []
        for param in params:
            o = DocObj()
            o.xml = param
            o.name = param.find("declname").text
            o.type = param.find("type")

            # Description will be filled in later if found
            o.description = None
            m.params.append(o)
    else:
        m.params = None

    if m.detaileddescription is not None:
        paramdescs = m.detaileddescription.findall(".//parameterlist")
        m.paramdescs = []

        for pd in paramdescs:
            #kind = pd.get("kind")
            ## Note use 'kind'
            
            # Note, should be just a simple object
            o = DocObj()
            o.names = []
            o.description = None

            for n in pd:
                names = n.findall("parameternamelist")
                o.description = n.find("parameterdescription")
                if names is not None:
                    for name in names:
                        o.names.append(name.text)
                        ## Note use direction and type
            
            m.paramdescs.append(o)
        
        if m.params is None and m.paramdescs is not None:
            print("Wait wut " + DocState.compound.name + "::" + m.name)
        # Set descriptions on the parameter objects
        for pd in m.paramdescs:
            for name in pd.names:
                for p in m.params:
                    if p.name is name:
                        p.description = pd.description
                        print("Found matching parameter " + p.name)
                        break


def gather_page_doc(xml):

    # xml
    # id
    # name
    # kind
    # briefdesc
    # detaileddesc
    # innerpage
    
    obj = xml.get("docobj")
    #id should already be set
    
    title = xml.find("title")
    if title is not None and title.text is not None:
        obj.name = formatname(title.text)
    else:
        obj.name = ""

    # title = xml.find("compoundname")

    obj.kind = xml.get("kind")
    obj.briefdescription = xml.find("briefdescription")
    obj.detaileddescription = xml.find("detaileddescription")

    obj.subpages = []
    for n in xml.findall("innerpage"):
        obj.subpages.append(n.get("ref"))

    for p in obj.subpages:
        p.parentpage = obj


def gather_namespace_doc(xml):
    
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
    obj.name = formatname(xml.find("compoundname").text)
    obj.kind = xml.get("kind")
    obj.briefdescription = xml.find("briefdescription")
    obj.detaileddescription = xml.find("detaileddescription")

    obj.innerclasses = []
    for node in xml.findall("innerclass"):
        obj.innerclasses.append(node.get("ref"))

    obj.innernamespaces = []
    for node in xml.findall("innernamespace"):
        obj.innernamespaces.append(node.get("ref"))

    obj.members = []

    for member in xml.findall("sectiondef/memberdef"):
        
        gather_member_doc(member)
        obj.members.append(member.get("docobj"))



def generate_compound_doc(xml):

    compound = xml.get("docobj")
    
    DocState.pushwriter()
    DocState.currentobj = compound

    if compound.kind is "class" or compound.kind is "struct":
        generate_class_doc(compound)
    elif compound.kind is "page":
        generate_page_doc(compound)
    elif compound.kind is "namespace":
        generate_namespace_doc(compound)
    else:
        print("Skipping " + compound.kind + " " + compound.name)
        DocState.popwriter()
        return

    f = file(compound.full_path(), "w")
    s = DocState.popwriter()
    f.write(s)
    f.close()

    assert DocState.empty_writerstack()

    #generage_page_doc(compound)

def generate_class_doc(compound):

    doxylayout.header()

    doxylayout.navheader()

    doxylayout.begin_content()
    doxylayout.pagetitle(compound.kind.title() + " " + compound.name)

    doxylayout.description(compound.briefdescription)
    doxylayout.description(compound.detaileddescription)

    doxylayout.members_list(compound)
    doxylayout.members(compound)

    doxylayout.end_content()
    doxylayout.footer()

def generate_page_doc(compound):

    doxylayout.header()

    doxylayout.navheader()

    doxylayout.begin_content()

    doxylayout.pagetitle(compound.name)

    doxylayout.description(compound.briefdescription)
    doxylayout.description(compound.detaileddescription)

    doxylayout.end_content()
    doxylayout.footer()

def generate_namespace_doc(compound):

    doxylayout.header()

    doxylayout.navheader()

    doxylayout.begin_content()
    doxylayout.pagetitle("Namespace " + compound.name)

    doxylayout.description(compound.briefdescription)
    doxylayout.description(compound.detaileddescription)

    doxylayout.namespace_list_inner(compound)

    doxylayout.end_content()
    doxylayout.footer()
