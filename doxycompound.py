from doxybase import DocState
import doxylayout
import doxytiny
from doxysettings import DocSettings


def process_references_root(root, state):

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
        id = node.get("refid")
        if id is not None:
            try:
                # Doxygen can sometimes generate refid=""
                obj = state.get_docobj(id)
                node.set("ref", obj)
            except KeyError:
                # print "Invalid refid: '" + id + "' in compound " + xml.find("compoundname").text
                # raise
                pass

    # for node in root.findall(".//*[@id]"):
    #    try:
    #        id = node.get("id")
    #        obj = docobjs[id]
    #        node.set("docobj", obj)
    #    except KeyError:
    #        pass


def pre_output():
    pass


def gather_entity_doc(entity):
    entity.read_from_xml()


def write_from_template(template, compound):
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

    write_from_template(template, compound)

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
