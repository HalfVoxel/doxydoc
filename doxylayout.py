from doxybase import DocState, JinjaFilter, dump
import doxytiny
from doxysettings import DocSettings
from str_tree import StrTree

INITIAL_HEADING_DEPTH = 2


def is_hidden(docobj):
    if docobj.hidden:
        return True
    return False


# def prettify_prefix(docobj):
#     s = []
#     prot = node.protection
#     if prot is not None:
#         prot = prot.title()
#         s.append(prot)

#     virt = node.virtual
#     if virt is not None and virt != "non-virtual":
#         s.append(virt)

#     # override = node.reimplements") is not None and virt == "virtual"

#     if override:
#         assert node.find("type").text
#         override_type = node.find("type").text.split()[0]
#         assert (
#            override_type != "override" and
#            override_type != "new"
#            ), "Invalid override type: " + override_type

#         s.append(override_type)

#     static = node.get("static")
#     if static == "yes":
#         s.append("static")

#     # mutable?

#     return " ".join(s)


def get_href(id):
    obj = DocState.get_docobj(id)
    return obj.full_url()


def get_anchor(id):
    obj = DocState.get_docobj(id)
    return obj.anchor


@JinjaFilter
def refcompound(refnode):
    result = StrTree()
    refid = refnode.get("refid")

    if refid == "":
        result += markup(refnode)
        return result

    assert refid, refnode.tag + " was not a ref node. " + refnode.text + " " + str(refnode.attrib)

    # kind = refnode.get("kindref")
    # external = refnode.get("external")
    tooltip = refnode.get("tooltip")
    obj = DocState.get_docobj(id)

    obj = obj.compound
    assert obj

    # Prevent recursive loops of links in the tooltips
    DocState.depth_ref += 1
    if DocState.depth_ref > 1 or is_hidden(obj):
        result += obj.name
    else:
        # Write out anchor element
        result.element("a", obj.name, {
            "href": obj.full_url(),
            "rel": 'tooltip',
            "data-original-title": tooltip
        })
    DocState.depth_ref -= 1
    return result


@JinjaFilter
def docobjref(obj):
    result = StrTree()
    # Prevent recursive loops of links in the tooltips
    DocState.depth_ref += 1
    if DocState.depth_ref > 1 or is_hidden(obj):
        result += obj.name
    else:
        if hasattr(obj, "briefdescription") and obj.briefdescription is not None:
            tooltip = description(obj.briefdescription)
        else:
            tooltip = None

        # Write out anchor element
        result.element("a", obj.name, {
            "href": obj.full_url(),
            "rel": 'tooltip',
            "data-original-title": tooltip
        })
    DocState.depth_ref -= 1
    return result


def ref(refnode):
    obj = refnode.get("ref")

    if obj is None:
        return markup(refnode)

    # assert refid, refnode.tag + " was not a ref node. " + refnode.text + " " + str(refnode.attrib)

    # kind = refnode.get("kindref")
    # external = refnode.get("external")
    # tooltip = refnode.get("tooltip")

    result = StrTree()
    DocState.depth_ref += 1
    if DocState.depth_ref > 1 or is_hidden(obj):
        result += markup(refnode)
    else:

        if hasattr(obj, "briefdescription") and obj.briefdescription is not None:
            tooltip = description(obj.briefdescription)
        else:
            tooltip = None

        result.element("a", None, {
            "href": obj.full_url(),
            "rel": 'tooltip',
            "data-original-title": tooltip
        })
        result += markup(refnode)
        result.element("/a")
    DocState.depth_ref -= 1
    return result


@JinjaFilter
def ref_explicit(obj, text, tooltip=None):
    result = StrTree()
    DocState.depth_ref += 1
    if DocState.depth_ref > 1 or is_hidden(obj):
        result += text
    else:
        result.element("a", text, {
            "href": obj.full_url(),
            "rel": 'tooltip',
            "data-original-title": tooltip
        })
    DocState.depth_ref -= 1
    return result


def match_external_ref(text):
    result = StrTree()
    words = text.split()
    for i in range(0, len(words)):
        if i > 0:
            result += " "
        try:
            obj = DocState.get_docobj("__external__" + words[i].strip())
            result += ref_explicit(obj, words[i], obj.tooltip if hasattr(obj, "tooltip") else None)
        except KeyError:
            result += words[i]

    return result


@JinjaFilter
def linked_text(node):
    result = StrTree()

    if node is None:
        return result

    if node.text is not None:
        result += match_external_ref(node.text)
        # result += node.text

    for n in node:
        if n.tag == "ref":
            result += ref(n)
        else:
            if n.text is not None:
                result += match_external_ref(n.text)

        if n.tail is not None:
            result += match_external_ref(n.tail)
            # result += n.tail

    return result


def header():
    return StrTree(DocSettings.header)


def footer():
    return StrTree(DocSettings.footer)


def begin_content():
    return StrTree("<div class='content'>")


def end_content():
    return StrTree("</div>")


def navheader():
    result = StrTree()
    result.append("<div class='navbar'><ul>")

    DocState.navitems.sort(key=lambda v: v.order)

    for item in DocState.navitems:
        result.element("li")
        result.element("a", item.label, {"href": item.ref.full_url()})
        result.element("/li")

    DocState.trigger("navheader")
    result.append("</div></ul>")
    return result


def pagetitle(title):
    return StrTree().element("h1", title)


def file_path(path):
    if path is None:
        return StrTree()

    return StrTree().element("span", path, {"class": "file-location"})


def member_section_heading(section):
    # skind = section.get("kind")
    # skind = skind.replace("-"," ")
    # skind = skind.replace("attrib","attributes")
    # skind = skind.replace("func","functions")
    # skind = skind.replace("property","properties")
    # skind = skind.title()

    return StrTree().element("h2", section[0])


def get_member_sections(compound, members):
    ''' Returns a list of sections in which to group members for display '''
    sections = []

    for m in members:
        if not hasattr(m, "protection"):
            dump(m)

# <xsd:simpleType name="DoxMemberKind">
#     <xsd:restriction base="xsd:string">
#       <xsd:enumeration value="define" />
#       <xsd:enumeration value="property" />
#       <xsd:enumeration value="event" />
#       <xsd:enumeration value="variable" />
#       <xsd:enumeration value="typedef" />
#       <xsd:enumeration value="enum" />
#       <xsd:enumeration value="function" />
#       <xsd:enumeration value="signal" />
#       <xsd:enumeration value="prototype" />
#       <xsd:enumeration value="friend" />
#       <xsd:enumeration value="dcop" />
#       <xsd:enumeration value="slot" />
#     </xsd:restriction>
#   </xsd:simpleType>

    our_methods = [m for m in members if m.compound == compound]
    instance_methods = [m for m in our_methods if not m.static]
    static_methods = [m for m in our_methods if m.static]

    public_instance_methods = [m for m in instance_methods if m.protection == "public"]
    public_static_methods = [m for m in static_methods if m.protection == "public"]

    sections.append((
        "Public Methods",
        [m for m in public_instance_methods if m.kind == "function"]
    ))
    sections.append((
        "Public Properties",
        [m for m in public_instance_methods if m.kind == "property"]
    ))
    sections.append((
        "Public Variables",
        [m for m in public_instance_methods if m.kind == "variable"]
    ))
    sections.append((
        "Public Events",
        [m for m in public_instance_methods if m.kind == "event"]
    ))
    sections.append((
        "Public Typedefs",
        [m for m in public_instance_methods if m.kind == "typedef"]
    ))
    sections.append((
        "Public Signals",
        [m for m in public_instance_methods if m.kind == "signal"]
    ))
    sections.append((
        "Public Prototypes",
        [m for m in public_instance_methods if m.kind == "prototype"]
    ))
    sections.append((
        "Public Friends",
        [m for m in public_instance_methods if m.kind == "friend"]
    ))
    sections.append((
        "Public Slots",
        [m for m in public_instance_methods if m.kind == "slot"]
    ))

    sections.append((
        "Public Static Methods",
        [m for m in public_static_methods if m.kind == "function"]
    ))
    sections.append((
        "Public Static Properties",
        [m for m in public_static_methods if m.kind == "property"]
    ))
    sections.append((
        "Public Static Variables",
        [m for m in public_static_methods if m.kind == "variable"]
    ))
    sections.append((
        "Public Static Variables",
        [m for m in public_static_methods if m.kind == "variable"]
    ))
    sections.append((
        "Public Static Events",
        [m for m in public_static_methods if m.kind == "event"]
    ))
    sections.append((
        "Public Static Typedefs",
        [m for m in public_static_methods if m.kind == "typedef"]
    ))
    sections.append((
        "Public Static Signals",
        [m for m in public_static_methods if m.kind == "signal"]
    ))
    sections.append((
        "Public Static Prototypes",
        [m for m in public_static_methods if m.kind == "prototype"]
    ))
    sections.append((
        "Public Static Friends",
        [m for m in public_static_methods if m.kind == "friend"]
    ))
    sections.append((
        "Public Static Slots",
        [m for m in public_static_methods if m.kind == "slot"]
    ))

    sections.append((
        "Private/Protected Members",
        filter(lambda m: m.protection != "public" and m.compound == compound, members)
    ))

    # Handling it specially
    # There no point explicitly showing an empty section when a class does no inherit any members
    ls = filter(lambda m: m.compound != compound, members)
    if len(ls) > 0:
        for v in ls:
            if v.name == "PostProcess":
                dump(v)

        sections.append(("Inherited Members", ls))

    # sections.append(("All Members", members))
    return sections


def member_list_protection(member):
    ''' Shows the protection of a member in the table/list view '''

    result = StrTree()
    result.element("span", member.protection.title())

    if member.readonly:
        result.element("span", "Readonly")
    if member.static:
        result.element("span", "Static")

    return result


def member_list_type(member):
    ''' Displays the member's type. Used in the members table '''

    if member.type is not None:
        # Write type
        return linked_text(member.type)
    else:
        return StrTree()


def enum_members(members):

    result = StrTree()
    result.element("ul", None, {'class': 'enum-members'})

    for m in members:
        result.element("li")

        result.element("p")
        result.element("b")
        result += ref_explicit(m, m.name)
        result += " "
        result.element("/b")
        if m.initializer is not None:
            result.element("span", lambda: linked_text(m.initializer))
        result.element("/p")

        result += description(m.briefdescription)
        result += description(m.detaileddescription)

        result.element("/td")
        result.element("/li")

    result.element("/ul")
    return result


def members_list(docobj):

    result = StrTree()
    result.element("div", None, {"class": "member-list"})

    sections = get_member_sections(docobj, docobj.all_members)

    for section in sections:

        members = section[1]

        if len(members) == 0:
            continue

        result.element("h2", section[0])

        result.element("table", None, {
            'class': 'table table-condensed table-striped member-list-section'
        })

        for m in members:
            result.element("tr")

            # Show protection in table if requested
            if DocSettings.show_member_protection_in_list:
                result.element("td", None, {'class': 'member-prot'})
                result += member_list_protection(m)
                result.element("/td")

            # Show type in table if requested
            if DocSettings.show_member_protection_in_list:
                result.element("td", None, {'class': 'member-type'})
                result += member_list_type(m)
                result.element("/td")

            result.element("td", None, {'class': 'member-name'})
            result += ref_explicit(m, m.name)
            # result += m.name
            result.element("/td")

            result.element("td", None, {'class': 'member-desc'})
            result += description(m.briefdescription)

            result.element("/td")

            result.element("/tr")

        result.element("/table")

    result.element("/div")
    return result


def members_section_empty_message(section):
    return StrTree().element("p", "Seems there are no members to be listed here", {
        "class": "empty-section"
    })


def members(docobj):
    result = StrTree()
    sections = get_member_sections(docobj, docobj.members)

    for section in sections:
        members = section[1]

        if not DocSettings.keep_empty_member_sections:
            if sum(not is_hidden(m) for m in members) == 0:
                continue

        result.html("<div class ='member-sec'>")

        result += member_section_heading(section)

        count = 0
        members = section[1]
        for m in members:
            # Ignore hidden members
            if not is_hidden(m):
                result += member(m)
                count += 1

        if count == 0:
            result += members_section_empty_message(section)

        result.html("</div>")

    return result


def member_heading(m):
    result = StrTree()
    result.element("h3")

    ls = []
    if m.protection is not None:
        ls.append(m.protection.title())
    if m.readonly:
        ls.append("readonly")
    if m.static:
        ls.append("static")

    result += ' '.join(ls)

    # These kinds of members have a () list
    if m.kind == "function":
        if len(ls) > 0:
            result.element("span", None, {"class": 'member-type'})

        # Write type
        result += linked_text(m.type)

    result.element("/span")
    result.element("span", None, {"class": 'member-name'})

    result += m.name

    result.element("/span")

    if m.params is not None:
        result += " "

        result.element("span", None, {"class": "member-params"})
        result += "("
        for i, param in enumerate(m.params):
            result += " "
            result += linked_text(param.type)

            result += " "

            if param.description is not None:
                tooltip = description(param.description)
                result.element("span", None, {"data-original-title": tooltip})
                result += param.name
                result.element("/span")
            else:
                result += param.name

            if i < len(m.params) - 1:
                result += ","

        result.element("/span")

    result.element("/h3")
    return result


@JinjaFilter
def member_parameter_name(param):
    result = StrTree()
    if param.description is not None:
        tooltip = description(param.description)
        result.element("span", None, {"data-original-title": tooltip})
        result += param.name
        result.element("/span")
    else:
        result += param.name
    return result


def desctitle(text):
    return StrTree().element("h3", text)


def sect(sectnode, depth):
    ''' sect* nodes '''

    result = StrTree()
    title = sectnode.find("title")
    if title is not None:
        result.element("h" + str(depth + INITIAL_HEADING_DEPTH), title.text, {
            "id": get_anchor(sectnode.get("id"))
        }
        )

    result += sectbase(sectnode)
    return result


def paragraph(paranode):
    ''' para nodes '''

    result = StrTree()
    result.elem("p")
    result += markup(paranode)
    result.elem("/p")
    return result


def markup(node):
    ''' Markup like nodes '''

    result = StrTree()
    if node is None:
        return result

    if node.text is not None:
        result += node.text

    # Traverse children
    for n in node:
        child_result = doxytiny.write_xml(n)
        if child_result is not None:
            result += child_result
        else:
            print("[W1] Not handled: " + n.tag)
            if n.text is not None:
                result += n.text

        if n.tail is not None:
            result += n.tail

    return result


def internal(internalnode):
    ''' internal nodes '''

    print("Skipping internal data")
    return StrTree()


def sectbase(node):
    result = StrTree()
    for n in node:
        if n == node:
            continue

        if n.tag == "para":
            result += paragraph(n)
        elif n.tag == "sect1":
            result += sect(n, 1)
        elif n.tag == "sect2":
            result += sect(n, 2)
        elif n.tag == "sect3":
            result += sect(n, 3)
        elif n.tag == "sect4":
            result += sect(n, 4)
        elif n.tag == "sect5":
            result += sect(n, 5)
        elif n.tag == "simplesectsep":
            result += doxytiny.simplesectsep(n)
        elif n.tag == "title":
            # A sect should have been the parent, so it should have been handled
            pass
        elif n.tag == "internal":
            result += internal(n)
        else:
            print("[W2] Not handled: " + n.tag)

    return result


@JinjaFilter
def description(descnode):
    result = StrTree()
    # \todo Ugly to have multiple possible types for description objects
    if isinstance(descnode, str):
        result += descnode
        return result

    if descnode is not None:
        title = descnode.find("title")
        if title is not None:
            result += desctitle(title.text)

        result += sectbase(descnode)

    return result


def member(m):

    result = StrTree()
    result.element("div", None, {"class": 'memberdef', "id": m.anchor})

    result += member_heading(m)

    result += description(m.briefdescription)
    result += description(m.detaileddescription)

    result.element("/div")


def get_inner_pages(obj):
    pages = []
    if obj is None:
        for k, obj2 in DocState._docobjs.iteritems():
            if (
                obj2.kind == "page" and
                (not hasattr(obj2, "parentpage") or obj2.parentpage is None) and
                obj2 not in pages and
                obj2.id != "indexpage"
            ):
                pages.append(obj2)
    else:
        pages = obj.subpages if obj.subpages is not None else []

    return pages


def page_list_inner(obj):
    result = StrTree()

    pages = get_inner_pages(obj)

    if pages is None or len(pages) == 0:
        return result

    result.element("ul")

    for p in pages:
        result.element("li")
        result += docobjref(p)
        result += page_list_inner(p)
        result.element("/li")

    result.element("/ul")
    return result


def group_list_inner_classes(objs):
    result = StrTree()
    result.element("table", None, {"class": "inner-class-list table table-condensed table-striped"})
    for n in objs:
        result.element("tr")
        result.element("td", lambda: docobjref(n))
        result.element("td", lambda: description(n.briefdescription))
        result.element("/tr")

    result.element("/table")
    return result


def group_list_inner_namespaces(objs):
    group_list_inner_classes(objs)


def group_list_inner_groups(objs):
    group_list_inner_classes(objs)


def file_list_inner_classes(obj):
    """
    Show a list of classes a file contains.
    \param obj A list of Entity
    """
    # \bug Either class, struct or interface
    result = StrTree()
    header_text = "This file defines the following class" + ("es" if len(obj) > 1 else "") + ":"
    result.element("h4", header_text)
    result.element("ul", None, {"class": "inner-class-list"})
    for n in obj:
        result.element("li", lambda: docobjref(n))

    result.element("/ul")
    return result


def file_list_inner_namespaces(obj):
    return StrTree()


def namespace_list_inner(obj):
    result = StrTree()
    result.element("table", None, {"class": "compound-view"})

    namespaces = []
    gridobjs = []
    if hasattr(obj, "innerclasses"):
        for obj2 in obj.innerclasses:
            if(obj2.kind == "class" or obj2.kind == "struct") and obj2 not in gridobjs:
                gridobjs.append(obj2)
    else:
        for k, obj2 in DocState._docobjs.iteritems():
            if(obj2.kind == "class" or obj2.kind == "struct") and obj2 not in gridobjs:
                gridobjs.append(obj2)

    if hasattr(obj, "innernamespaces"):
        for ns in obj.innernamespaces:
            namespaces.append(ns)
    else:
        for k, obj2 in DocState._docobjs.iteritems():
            if obj2.kind == "namespace" and obj2 not in namespaces:
                if hasattr(obj2, "innerclasses") and len(obj2.innerclasses) > 0:
                    namespaces.append(obj2)

    # Apparently, this manages to sort them by name.
    # Even without me specifying what to sort by.
    # Python...
    gridobjs.sort()
    namespaces.sort()

    # Number of columns
    xwidth = 4
    ns_colspan = int(xwidth / 2)

    counter = 0

    for obj2 in namespaces:
        if counter % xwidth is 0:
            if counter > 0:
                result.element("/tr")
            result.element("tr")

        result.element("td", None, {"colspan": str(ns_colspan)})
        DocState.depth_ref += 1
        result.element("a", None, {"href": obj2.full_url()})
        result.element("b", obj2.name)

        # result += doxylayout.docobjref(obj2)
        # result.element("p")
        result += description(obj2.briefdescription)
        # result.element("/p")
        result.element("/a")
        result.element("/td")

        counter += ns_colspan

        DocState.depth_ref -= 1

    if(len(namespaces) > 0):
        result.element("/tr")

    counter = 0
    for obj2 in gridobjs:
        # NOTE: Add enum
        if counter % xwidth == 0:
            if counter > 0:
                result.element("/tr")
            result.element("tr")

        result.element("td")

        DocState.depth_ref += 1
        result.element("a", None, {"href": obj2.full_url()})
        result.element("b", obj2.name)

        # result += doxylayout.docobjref(obj2)
        # result.element("p")
        result += description(obj2.briefdescription)
        # result.element("/p")
        result.element("/a")
        result.element("/td")
        DocState.depth_ref -= 1

        counter += 1

    result.element("/tr")
    result.element("/table")
    return result


def namespace_inner_class(obj):
    result = StrTree()
    result.elem("li")
    result += docobjref(obj)
    result.elem("/li")
    return result
