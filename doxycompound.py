from doxybase import *
#import doxyext
import doxylayout
import re
import doxytiny
from doxysettings import DocSettings
import jinja2

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
    
    if compound.kind == "class" or compound.kind == "struct" or compound.kind == "interface":
        gather_class_doc(xml)
    elif compound.kind == "page":
        gather_page_doc(xml)
    elif compound.kind == "namespace":
        gather_namespace_doc(xml)
    elif compound.kind == "file":
        gather_file_doc(xml)
    elif compound.kind == "example":
        gather_example_doc(xml)
    elif compound.kind == "group":
        gather_group_doc(xml)
    else:
        if DocSettings.args.verbose:
            print("Skipping " + compound.kind + " " + compound.name)
        return

def formatname(t):
    return t.replace("::", ".")

''' Returns if the member's detailed view should be hidden '''
def is_detail_hidden(member):

    # Enums show up as members, but they should always be shown.
    if member.kind == "enum":
        return False

    # Check if the member is undocumented
    if DocSettings.hide_undocumented and (member.detaileddescription.text is None or member.detaileddescription.text.isspace()):
        if member.detaileddescription.text is None:
            return True

        count = 0
        for v in member.detaileddescription.iter():
            count += 1
            if (count > 1):
                break

        # If we only visited the root node (member.detaileddescription), then it has no children and so the detaileddescription is empty
        if count == 1:
            return True

    return False

def gather_group_doc(xml):

    # name
    # kind
    # briefdesc
    # detaileddesc
        
    obj = xml.get("docobj")
    #id should already be set
    obj.name = formatname(xml.find("compoundname").text)
    obj.title = formatname(xml.find("title").text)
    obj.briefdescription = xml.find("briefdescription")
    obj.detaileddescription = xml.find("detaileddescription")

    obj.innerclasses = [node.get("ref") for node in xml.findall("innerclass")]
    obj.innernamespaces = [node.get("ref") for node in xml.findall("innernamespace")]

    obj.innergroups = [node.get("ref") for node in xml.findall("innergroup")]

def gather_example_doc(xml):

    # name
    # kind
    # briefdesc
    # detaileddesc
        
    obj = xml.get("docobj")
    #id should already be set
    obj.name = formatname(xml.find("compoundname").text)
    obj.briefdescription = xml.find("briefdescription")
    obj.detaileddescription = xml.find("detaileddescription")

def gather_file_doc(xml):

    # name
    # kind
    # briefdesc
    # detaileddesc
    # innerclasses
    # innernamespaces
    # contents (programlisting)
    # location
        
    obj = xml.get("docobj")
    #id should already be set
    obj.name = formatname(xml.find("compoundname").text)
    obj.briefdescription = xml.find("briefdescription")
    obj.detaileddescription = xml.find("detaileddescription")

    obj.innerclasses = []
    for node in xml.findall("innerclass"):
        obj.innerclasses.append(node.get("ref"))

    obj.innernamespaces = []
    for node in xml.findall("innernamespace"):
        obj.innernamespaces.append(node.get("ref"))

    obj.contents = xml.find("programlisting")

    gather_members(xml)
    # Only one members list
    obj.all_members = obj.members

    # Find location of file
    loc = xml.find("location")
    obj.location = loc.get("file") if loc is not None else None

    if not DocSettings.show_source_files:
        obj.hidden = True

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
    gather_members(xml)

    obj.briefdescription = xml.find("briefdescription")
    obj.detaileddescription = xml.find("detaileddescription")
    
    obj.final = xml.get("final") == "yes"
    obj.sealed = xml.get("sealed") == "yes"
    obj.abstract = xml.get("abstract") == "yes"

    obj.inherited = []
    for node in xml.findall("basecompoundref"):
        obj.inherited.append(node.get("ref"))

    obj.derived = []
    for node in xml.findall("derivedcompoundref"):
        obj.derived.append(node.get("ref"))

    # All members, also inherited ones
    obj.all_members = [m.get("ref") for m in xml.find("listofallmembers")]
    for m in xml.find("listofallmembers"):
        if m.get("ref") is None:
            print ("NULL REFERENCE " + m.find("name").text + " " + m.find("scope").text)
            print ("Sure not old files are in the xml directory")

def gather_members(xml):
    obj = xml.get("docobj")

    obj.members = []
    for member in xml.findall("sectiondef/memberdef"):
        
        gather_member_doc(member)
        obj.members.append(member.get("docobj"))

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
    if virt is not None and virt != "non-virtual":
        m.virtual = virt
    else:
        m.virtual = None

    m.static = member.get("static") == "yes"

    m.reimplementedby = []
    for reimp in member.findall("reimplementedby"):
        obj = reimp.get("ref")
        m.reimplementedby.append(obj)

    m.reimplements = []
    for reimp in member.findall("reimplements"):
        obj = reimp.get("ref")
        m.reimplements.append(obj)
    
    override = len(m.reimplements) > 0 and m.virtual == "virtual"

    if override:
        assert member.find("type").text
        types = member.find("type").text.split()
        overrideType = None
        if "override" in types:
            overrideType = "override"
        if "new" in types:
            print types, overrideType, m.id
            assert(overrideType is None)
            overrideType = "new"

        override = overrideType

        # For abstract classes or interfaces, it might reimplement some function without overriding it
        # thus the need to check again here
        m.override = overrideType
    else:
        m.override = None


    # Find descriptions
    m.briefdescription = member.find("briefdescription")
    m.detaileddescription = member.find("detaileddescription")

    m.initializer = member.find("initializer")

    if m.kind != "enum":
        # Find type
        m.type = member.find("type")

        # Is the member read only. Doxygen will put 'readonly' at the start of the 'type' field if it is readonly
        m.readonly = False if m.type is None or m.type.text is None else "readonly " in m.type.text
        
        if m.type is not None and m.type.text is not None:
            # Remove eventual 'override ' text at start of type.
            m.type.text = re.sub("(?:override|new|readonly|abstract)\s", "", m.type.text, 1)
    else:
        m.type = None
        m.readonly = False

        vals = member.findall("enumvalue")
        m.members = []
        for val in vals:
            # Doxygen does not set the kind for these members, so we set it here for simplicity
            val.set("kind", "enumvalue")
            gather_member_doc(val)
            m.members.append(val.get("docobj"))

        # Only one members list
        m.all_members = m.members

    # Parse(function) arguments
    argsstring = member.find("argsstring")
    # Test if this member has arguments(.text will be None if the tag is empty)
    if argsstring is not None and argsstring.text is not None:
        m.argsstring = argsstring.text

        m.hasparams = True
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
        m.hasparams = False
        m.params = []

    if m.detaileddescription is not None:
        paramdescs = m.detaileddescription.findall(".//parameterlist")
        m.paramdescs = []

        ### TODO, Take care of 'Exception' "parameters"
        
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
        
        if m.params is None and len(m.paramdescs) > 0:
            print("Wait wut " + DocState.compound.name + "::" + m.name)
       
        # Set descriptions on the parameter objects
        for pd in m.paramdescs:
            for name in pd.names:
                for p in m.params:
                    if p.name == name:
                        p.description = pd.description
                        print("Found matching parameter " + p.name)
                        break


    # Depending on settings, this object be hidden
    # If .hidden is true, no links to it will be generated, instead just plain text
    m.hidden = is_detail_hidden(m)

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

    obj.innerpages = obj.subpages


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

    gather_members(xml)


def write_from_template (template, compound):
    DocState.currentobj = compound
    f = file(compound.full_path(), "w")
    s = DocState.environment.get_template(template + ".html").render(compound=compound, doxylayout=doxylayout, DocState=DocState)
    f.write(s)
    f.close()

    assert DocState.empty_writerstack()

def generate_compound_doc(compound):
    

    if compound.hidden:
        return

    template = ""
    if compound.kind == "class" or compound.kind == "struct":
        template = "classdoc"
    elif compound.kind == "page":
        template = "pagedoc"
    elif compound.kind == "namespace":
        template = "namespacedoc"
    elif compound.kind == "file":
        template = "filedoc"
    elif compound.kind == "example":
        template = "exampledoc"
    elif compound.kind == "group":
        template = "groupdoc"
    elif compound.kind == "enum":
        template = "enumdoc"
        return
    else:
        if DocSettings.args.verbose:
            print("Skipping " + compound.kind + " " + compound.name)
        return

    write_from_template(template,compound)

    return

    DocState.pushwriter()

    try:
        if compound.kind == "class" or compound.kind == "struct":
            generate_class_doc(compound)
        elif compound.kind == "page":
            generate_page_doc(compound)
        elif compound.kind == "namespace":
            generate_namespace_doc(compound)
        elif compound.kind == "file":
            generate_file_doc(compound)
        elif compound.kind == "example":
            generate_example_doc(compound)
        elif compound.kind == "group":
            generate_group_doc(compound)
        elif compound.kind == "enum":
            generate_enum_doc(compound)
        else:
            if DocSettings.args.verbose:
                print("Skipping " + compound.kind + " " + compound.name)
            DocState.popwriter()
            return

        f = file(compound.full_path(), "w")
        s = DocState.popwriter()
        f.write(s)
        f.close()

        assert DocState.empty_writerstack()
    except:
        print (DocState.currentobj)
        raise

def generate_enum_doc(compound):
    doxylayout.header()

    doxylayout.navheader()

    doxylayout.begin_content()

    def title():
        DocState.writer.element("span", compound.kind.title(), {"class": "compound-kind"})
        DocState.writer.element("span", " " + compound.name)

    doxylayout.pagetitle(title)

    doxylayout.description(compound.briefdescription)
    doxylayout.description(compound.detaileddescription)

    doxylayout.enum_members(compound.members)

    doxylayout.end_content()
    doxylayout.footer()

def generate_group_doc(compound):
    
    doxylayout.header()

    doxylayout.navheader()

    doxylayout.begin_content()

    def title():
        DocState.writer.element("span", compound.kind.title(), {"class": "compound-kind"})
        DocState.writer.element("span", " " + compound.title)

    doxylayout.pagetitle(title)

    doxylayout.description(compound.briefdescription)
    doxylayout.description(compound.detaileddescription)

    doxylayout.group_list_inner_groups(compound.innergroups)
    doxylayout.group_list_inner_classes(compound.innerclasses)
    doxylayout.group_list_inner_namespaces(compound.innernamespaces)

    doxylayout.end_content()
    doxylayout.footer()

def generate_example_doc(compound):

    doxylayout.header()

    doxylayout.navheader()

    doxylayout.begin_content()

    def title():
        DocState.writer.element("span", compound.kind.title(), {"class": "compound-kind"})
        DocState.writer.element("span", " " + compound.name)

    doxylayout.pagetitle(title)

    doxylayout.description(compound.briefdescription)
    doxylayout.description(compound.detaileddescription)

    doxylayout.end_content()
    doxylayout.footer()

def generate_file_doc(compound):

    doxylayout.header()

    doxylayout.navheader()

    doxylayout.begin_content()

    def title():
        DocState.writer.element("span", compound.kind.title(), {"class": "compound-kind"})
        DocState.writer.element("span", " " + compound.name)

    doxylayout.pagetitle(title)

    if DocSettings.show_file_paths:
        doxylayout.file_path(compound.location)

    doxylayout.description(compound.briefdescription)
    doxylayout.description(compound.detaileddescription)

    if len(compound.innerclasses) > 0:
        doxylayout.file_list_inner_classes(compound.innerclasses)

    if len(compound.innernamespaces) > 0:
        doxylayout.file_list_inner_namespaces(compound.innernamespaces)

    doxytiny.programlisting(compound.contents)
    doxylayout.end_content()
    doxylayout.footer()

def generate_class_doc(compound):

    doxylayout.header()

    doxylayout.navheader()

    doxylayout.begin_content()

    def title():
        DocState.writer.element("span", compound.kind.title(), {"class": "compound-kind"})
        DocState.writer.element("span", " " + compound.name)

    doxylayout.pagetitle(title)

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
    
    def title():
        DocState.writer.element("span", compound.kind.title(), {"class": "compound-kind"})
        DocState.writer.element("span", " " + compound.name)

    doxylayout.pagetitle(title)

    doxylayout.description(compound.briefdescription)
    doxylayout.description(compound.detaileddescription)

    doxylayout.namespace_list_inner(compound)

    doxylayout.end_content()
    doxylayout.footer()
