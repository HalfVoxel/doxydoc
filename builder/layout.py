import builder.elements
from .str_tree import StrTree
from .writing_context import WritingContext

INITIAL_HEADING_DEPTH = 2


def is_hidden(docobj):
    # if docobj.hidden:
    #     return True
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


def get_anchor(ctx: WritingContext, id: str) -> str:
    # sect nodes are sometimes left without an id
    # Error on the user side, but check for this
    # to improve compatibility
    if id == "":
        return ""
    obj = ctx.state.get_entity(id)
    return obj.path.anchor


def refcompound(ctx: WritingContext, refnode, buffer: StrTree) -> None:
    refid = refnode.get("refid")

    if refid == "":
        markup(ctx, refnode, buffer)
        return

    assert refid, refnode.tag + " was not a ref node. " + refnode.text + " " + str(refnode.attrib)

    # kind = refnode.get("kindref")
    # external = refnode.get("external")
    tooltip = refnode.get("tooltip")
    obj = ctx.state.get_entity(id)

    obj = obj.compound
    assert obj

    # Prevent recursive loops of links in the tooltips

    if ctx.strip_links or is_hidden(obj):
        buffer += obj.name
    else:
        # Write out anchor element
        buffer.element("a", obj.name, {
            "href": ctx.relpath(obj.path.full_url()),
            "rel": 'tooltip',
            "data-original-title": tooltip
        })


def ref_entity(ctx: WritingContext, obj, buffer: StrTree) -> None:
    # Prevent recursive loops of links in the tooltips
    if ctx.strip_links or is_hidden(obj):
        buffer += obj.name
    else:
        tooltip = StrTree()
        _tooltip(ctx, obj, tooltip)

        # Write out anchor element
        buffer.element("a", obj.name, {
            "href": ctx.relpath(obj.path.full_url()),
            "rel": 'tooltip',
            "data-original-title": str(tooltip)
        })


def _tooltip(ctx: WritingContext, entity, buffer: StrTree) -> None:
    if entity.briefdescription is not None:
        description(ctx.with_link_stripping(), entity.briefdescription, buffer)


def ref(ctx: WritingContext, refnode, buffer) -> None:
    obj = ctx.getref(refnode)

    if obj is None:
        markup(ctx, refnode, buffer)
        return

    # assert refid, refnode.tag + " was not a ref node. " + refnode.text + " " + str(refnode.attrib)

    # kind = refnode.get("kindref")
    # external = refnode.get("external")
    # tooltip = refnode.get("tooltip")

    if ctx.strip_links or is_hidden(obj):
        markup(ctx, refnode, buffer)
    else:
        tooltip = StrTree()
        _tooltip(ctx, obj, tooltip)
        buffer.open("a", {
            "href": ctx.relpath(obj.path.full_url()),
            "rel": 'tooltip',
            "data-original-title": tooltip
        })
        markup(ctx.with_link_stripping(), refnode, buffer)
        buffer.close("a")


def ref_explicit(ctx: WritingContext, obj, text, tooltip, buffer: StrTree) -> None:
    if ctx.strip_links or is_hidden(obj):
        buffer += text
    else:
        if tooltip is None:
            tooltip = StrTree()
            _tooltip(ctx, obj, tooltip)

        buffer.element("a", text, {
            "href": ctx.relpath(obj.path.full_url()),
            "rel": 'tooltip',
            "data-original-title": tooltip
        })


def match_external_ref(ctx: WritingContext, text, buffer: StrTree) -> None:
    words = text.split()
    for i in range(0, len(words)):
        if i > 0:
            buffer += " "
        try:
            obj = ctx.state.get_entity("__external__" + words[i].strip())
            tooltip = obj.tooltip if hasattr(obj, "tooltip") else None
            ref_explicit(ctx, obj, words[i], tooltip, buffer)
        except KeyError:
            buffer += words[i]


def linked_text(ctx: WritingContext, node, buffer: StrTree) -> None:
    if node is None:
        return

    if node.text is not None:
        match_external_ref(ctx, node.text, buffer)
        # buffer += node.text

    for n in node:
        if n.tag == "ref":
            ref(ctx, n, buffer)
        else:
            if n.text is not None:
                match_external_ref(ctx, n.text, buffer)

        if n.tail is not None:
            match_external_ref(ctx, n.tail, buffer)


# def navheader():
#     buffer = StrTree()
#     buffer.append("<div class='navbar'><ul>")

#     Importer.navitems.sort(key=lambda v: v.order)

#     for item in Importer.navitems:
#         buffer.open("li")
#         buffer.element("a", item.label, {"href": item.ref.path.full_url()})
#         buffer.close("li")

#     Importer.trigger("navheader")
#     buffer.append("</div></ul>")
#     return buffer


def pagetitle(title, buffer: StrTree) -> None:
    buffer.element("h1", title)


def file_path(path, buffer: StrTree) -> None:
    if path is not None:
        buffer.element("span", path, {"class": "file-location"})


def member_section_heading(section, buffer: StrTree) -> None:
    # skind = section.get("kind")
    # skind = skind.replace("-"," ")
    # skind = skind.replace("attrib","attributes")
    # skind = skind.replace("func","functions")
    # skind = skind.replace("property","properties")
    # skind = skind.title()

    buffer.element("h2", section[0])


def member_list_protection(member, buffer: StrTree) -> None:
    ''' Shows the protection of a member in the table/list view '''

    buffer.element("span", member.protection.title())

    if member.readonly:
        buffer.element("span", "Readonly")
    if member.static:
        buffer.element("span", "Static")


def member_list_type(ctx: WritingContext, member, buffer: StrTree) -> None:
    ''' Displays the member's type. Used in the members table '''

    if member.type is not None:
        # Write type
        linked_text(ctx, member.type, buffer)


# def enum_members(ctx: WritingContext, members):

#     result = StrTree()
#     result.element("ul", None, {'class': 'enum-members'})

#     for m in members:
#         result.open("li")

#         result.open("p")
#         result.open("b")
#         result += ref_explicit(ctx, m, m.name, None)
#         result += " "
#         result.close("b")
#         if m.initializer is not None:
#             result.element("span", lambda: linked_text(ctx, m.initializer))
#         result.close("p")

#         result += description(ctx, m.briefdescription)
#         result += description(ctx, m.detaileddescription)

#         result.close("td")
#         result.close("li")

#     result.close("ul")
#     return result


# def members_list(docobj):

#     result = StrTree()
#     result.element("div", None, {"class": "member-list"})

#     sections = get_member_sections(docobj, docobj.all_members)

#     for section in sections:

#         members = section[1]

#         if len(members) == 0:
#             continue

#         result.element("h2", section[0])

#         result.element("table", None, {
#             'class': 'table table-condensed table-striped member-list-section'
#         })

#         for m in members:
#             result.open("tr")

#             # Show protection in table if requested
#             if DocSettings.show_member_protection_in_list:
#                 result.element("td", None, {'class': 'member-prot'})
#                 result += member_list_protection(m)
#                 result.close("td")

#             # Show type in table if requested
#             if DocSettings.show_member_protection_in_list:
#                 result.element("td", None, {'class': 'member-type'})
#                 result += member_list_type(m)
#                 result.close("td")

#             result.element("td", None, {'class': 'member-name'})
#             result += ref_explicit(ctx, m, m.name, None)
#             # result += m.name
#             result.close("td")

#             result.element("td", None, {'class': 'member-desc'})
#             result += description(m.briefdescription)

#             result.close("td")

#             result.close("tr")

#         result.close("table")

#     result.close("div")
#     return result


# def members_section_empty_message(section):
#     return StrTree().element("p", "Seems there are no members to be listed here", {
#         "class": "empty-section"
#     })


# def members(docobj):
#     result = StrTree()
#     sections = get_member_sections(docobj, docobj.members)

#     for section in sections:
#         members = section[1]

#         if not DocSettings.keep_empty_member_sections:
#             if sum(not is_hidden(m) for m in members) == 0:
#                 continue

#         result.html("<div class ='member-sec'>")

#         result += member_section_heading(section)

#         count = 0
#         members = section[1]
#         for m in members:
#             # Ignore hidden members
#             if not is_hidden(m):
#                 result += member(m)
#                 count += 1

#         if count == 0:
#             result += members_section_empty_message(section)

#         result.html("</div>")

#     return result


# def member_heading(m):
#     result = StrTree()
#     result.open("h3")

#     ls = []
#     if m.protection is not None:
#         ls.append(m.protection.title())
#     if m.readonly:
#         ls.append("readonly")
#     if m.static:
#         ls.append("static")

#     result += ' '.join(ls)

#     # These kinds of members have a () list
#     if m.kind == "function":
#         if len(ls) > 0:
#             result.element("span", None, {"class": 'member-type'})

#         # Write type
#         result += linked_text(m.type)

#     result.close("span")
#     result.element("span", None, {"class": 'member-name'})

#     result += m.name

#     result.close("span")

#     if m.params is not None:
#         result += " "

#         result.element("span", None, {"class": "member-params"})
#         result += "("
#         for i, param in enumerate(m.params):
#             result += " "
#             result += linked_text(param.type)

#             result += " "

#             if param.description is not None:
#                 tooltip = description(param.description)
#                 result.element("span", None, {"data-original-title": tooltip})
#                 result += param.name
#                 result.close("span")
#             else:
#                 result += param.name

#             if i < len(m.params) - 1:
#                 result += ","

#         result.close("span")

#     result.close("h3")
#     return result


def desctitle(ctx: WritingContext, text, buffer: StrTree) -> None:
    buffer.element("h3", text)


def sect(ctx: WritingContext, sectnode, depth, buffer: StrTree) -> None:
    ''' sect* nodes '''

    title = sectnode.find("title")
    if title is not None:
        buffer.element("h" + str(depth + INITIAL_HEADING_DEPTH), title.text, {
            "id": get_anchor(ctx, sectnode.get("id"))
        }
        )

    sectbase(ctx, sectnode, buffer)


def paragraph(ctx: WritingContext, paranode, buffer: StrTree) -> None:
    ''' para nodes '''

    buffer.open("p")
    markup(ctx, paranode, buffer)
    buffer.close("p")


def markup(ctx: WritingContext, node, buffer: StrTree) -> None:
    ''' Markup like nodes '''

    if node is None:
        return

    if node.text is not None:
        buffer += node.text

    # Traverse children
    for n in node:
        builder.elements.write_xml(ctx, n, buffer)

        if n.tail is not None:
            buffer += n.tail


def internal(ctx: WritingContext, internalnode, buffer: StrTree) -> None:
    ''' internal nodes '''

    print("Skipping internal data")


def sectbase(ctx: WritingContext, node, buffer: StrTree) -> None:
    for n in node:
        if n == node:
            continue

        if n.tag == "para":
            paragraph(ctx, n, buffer)
        elif n.tag == "sect1":
            sect(ctx, n, 1, buffer)
        elif n.tag == "sect2":
            sect(ctx, n, 2, buffer)
        elif n.tag == "sect3":
            sect(ctx, n, 3, buffer)
        elif n.tag == "sect4":
            sect(ctx, n, 4, buffer)
        elif n.tag == "sect5":
            sect(ctx, n, 5, buffer)
        elif n.tag == "simplesectsep":
            builder.elements.simplesectsep(ctx, n, buffer)
        elif n.tag == "title":
            # A sect should have been the parent, so it should have been handled
            pass
        elif n.tag == "internal":
            internal(ctx, n, buffer)
        else:
            print("[W2] Not handled: " + n.tag)


def description(ctx: WritingContext, descnode, buffer: StrTree) -> None:
    # \todo Ugly to have multiple possible types for description objects
    if isinstance(descnode, str):
        # TODO: Doesn't seem to happen
        buffer += descnode
        return

    if descnode is not None:
        title = descnode.find("title")
        if title is not None:
            desctitle(ctx, title.text, buffer)

        sectbase(ctx, descnode, buffer)


# def get_inner_pages(obj):
#     pages = []
#     if obj is None:
#         for k, obj2 in Importer._docobjs.iteritems():
#             if (
#                 obj2.kind == "page" and
#                 (not hasattr(obj2, "parentpage") or obj2.parentpage is None) and
#                 obj2 not in pages and
#                 obj2.id != "indexpage"
#             ):
#                 pages.append(obj2)
#     else:
#         pages = obj.subpages if obj.subpages is not None else []

#     return pages


# def page_list_inner(obj):
#     result = StrTree()

#     pages = get_inner_pages(obj)

#     if pages is None or len(pages) == 0:
#         return result

#     result.open("ul")

#     for p in pages:
#         result.open("li")
#         result += ref_entity(p)
#         result += page_list_inner(p)
#         result.close("li")

#     result.close("ul")
#     return result


# def group_list_inner_classes(objs):
#     result = StrTree()
#     result.element("table", None, {
#        "class": "inner-class-list table table-condensed table-striped"})
#     for n in objs:
#         result.open("tr")
#         result.element("td", lambda: ref_entity(n))
#         result.element("td", lambda: description(n.briefdescription))
#         result.close("tr")

#     result.close("table")
#     return result


# def file_list_inner_classes(obj):
#     """
#     Show a list of classes a file contains.
#     \param obj A list of Entity
#     """
#     # \bug Either class, struct or interface
#     result = StrTree()
#     header_text = "This file defines the following class" + ("es" if len(obj) > 1 else "") + ":"
#     result.element("h4", header_text)
#     result.element("ul", None, {"class": "inner-class-list"})
#     for n in obj:
#         result.element("li", lambda: ref_entity(n))

#     result.close("ul")
#     return result


# def file_list_inner_namespaces(obj):
#     return StrTree()


# def namespace_list_inner(obj):
#     result = StrTree()
#     result.element("table", None, {"class": "compound-view"})

#     namespaces = []
#     gridobjs = []
#     if hasattr(obj, "inner_classes"):
#         for obj2 in obj.inner_classes:
#             if(obj2.kind == "class" or obj2.kind == "struct") and obj2 not in gridobjs:
#                 gridobjs.append(obj2)
#     else:
#         for k, obj2 in Importer._docobjs.iteritems():
#             if(obj2.kind == "class" or obj2.kind == "struct") and obj2 not in gridobjs:
#                 gridobjs.append(obj2)

#     if hasattr(obj, "inner_namespaces"):
#         for ns in obj.inner_namespaces:
#             namespaces.append(ns)
#     else:
#         for k, obj2 in Importer._docobjs.iteritems():
#             if obj2.kind == "namespace" and obj2 not in namespaces:
#                 if hasattr(obj2, "inner_classes") and len(obj2.inner_classes) > 0:
#                     namespaces.append(obj2)

#     # Apparently, this manages to sort them by name.
#     # Even without me specifying what to sort by.
#     # Python...
#     gridobjs.sort()
#     namespaces.sort()

#     # Number of columns
#     xwidth = 4
#     ns_colspan = int(xwidth / 2)

#     counter = 0

#     for obj2 in namespaces:
#         if counter % xwidth is 0:
#             if counter > 0:
#                 result.close("tr")
#             result.open("tr")

#         result.element("td", None, {"colspan": str(ns_colspan)})
#         Importer.depth_ref += 1
#         result.element("a", None, {"href": obj2.path.full_url()})
#         result.element("b", obj2.name)

#         # result += doxylayout.ref_entity(obj2)
#         # result.open("p")
#         result += description(obj2.briefdescription)
#         # result.close("p")
#         result.close("a")
#         result.close("td")

#         counter += ns_colspan

#         Importer.depth_ref -= 1

#     if(len(namespaces) > 0):
#         result.close("tr")

#     counter = 0
#     for obj2 in gridobjs:
#         # NOTE: Add enum
#         if counter % xwidth == 0:
#             if counter > 0:
#                 result.close("tr")
#             result.open("tr")

#         result.open("td")

#         Importer.depth_ref += 1
#         result.element("a", None, {"href": obj2.path.full_url()})
#         result.element("b", obj2.name)

#         # result += doxylayout.ref_entity(obj2)
#         # result.open("p")
#         result += description(obj2.briefdescription)
#         # result.close("p")
#         result.close("a")
#         result.close("td")
#         Importer.depth_ref -= 1

#         counter += 1

#     result.close("tr")
#     result.close("table")
#     return result


# def namespace_inner_class(obj):
#     result = StrTree()
#     result.open("li")
#     result += ref_entity(obj)
#     result.close("li")
#     return result
