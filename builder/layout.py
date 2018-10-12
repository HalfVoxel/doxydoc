import builder.elements
from .str_tree import StrTree
from .writing_context import WritingContext
from importer.entities import Entity

INITIAL_HEADING_DEPTH = 2


def is_hidden(docobj):
    # if docobj.hidden:
    #     return True
    return False

def get_anchor(ctx: WritingContext, id: str) -> str:
    # sect nodes are sometimes left without an id
    # Error on the user side, but check for this
    # to improve compatibility
    if id == "":
        return ""
    obj = ctx.state.get_entity(id)

    return obj.path.anchor


def get_local_anchor(ctx: WritingContext, entity: Entity, buffer: StrTree) -> None:
    assert entity is not None
    buffer.append(ctx.page.get_local_anchor(entity))


def refcompound(ctx: WritingContext, refnode, buffer: StrTree) -> None:
    refid = refnode.get("refid")

    if refid == "":
        markup(ctx, refnode, buffer)
        return

    assert refid, refnode.tag + " was not a ref node. " + refnode.text + " " + str(refnode.attrib)

    # kind = refnode.get("kindref")
    # external = refnode.get("external")
    tooltip = refnode.get("tooltip")
    obj = ctx.state.get_entity(refid)

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
    ref_entity_with_contents(ctx, obj, "", buffer)

def ref_entity_with_contents(ctx: WritingContext, obj, contents: str, buffer: StrTree) -> None:
    # Prevent recursive loops of links in the tooltips
    if ctx.strip_links or is_hidden(obj):
        buffer += obj.name
    else:
        tooltip = StrTree()
        _tooltip(ctx, obj, tooltip)

        # Write out anchor element
        buffer.open("a", {
            "href": ctx.relpath(obj.path.full_url()),
            "rel": 'tooltip',
            "data-original-title": str(tooltip)
        })
        buffer.html(contents)
        buffer.append(obj.name)
        buffer.close("a")


def _tooltip(ctx: WritingContext, entity, buffer: StrTree) -> None:
    if entity.briefdescription is not None:
        description(ctx.with_link_stripping(), entity.briefdescription, buffer)


def ref(ctx: WritingContext, refnode, buffer: StrTree) -> None:
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
            "rel": "tooltip",
            "data-original-title": tooltip
        })


def match_external_ref(ctx: WritingContext, text, buffer: StrTree) -> None:
    words = text.split()
    skipNextSpace = False
    for i in range(0, len(words)):
        w = words[i].strip()
        if w == ">":
            buffer += w
            continue

        ltStr = "<"
        lt = w.endswith(ltStr)
        if lt:
            w = w[:-len(ltStr)]

        if i > 0:
            if skipNextSpace:
                skipNextSpace = False
            else:
                buffer += " "
        try:
            obj = ctx.state.get_entity("__external__" + w.strip())
            tooltip = obj.tooltip if hasattr(obj, "tooltip") else None
            ref_explicit(ctx, obj, w, tooltip, buffer)
        except KeyError:
            buffer += w

        if lt:
            buffer += ltStr
            skipNextSpace = True


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
