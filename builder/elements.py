# coding=UTF-8

from .str_tree import StrTree
import builder.layout
import xml.etree.ElementTree as ET
import os
from .writing_context import WritingContext
from typing import List, Tuple
from importer.entities import Entity


def linebreak(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer.voidelem("br")


def hruler(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass


def preformatted(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer.element("pre", n.text)


def findIndent(parent: ET.Element):
    indent = 0
    empty = True
    for child in parent:
        if child.text is not None:
            empty = False
            break

        if child.tag == "sp":
            indent += 1

        subIndent, subEmpty = findIndent(child)
        empty &= subEmpty
        indent += subIndent

        if child.tail is not None:
            empty = False
            break

    return indent, empty


def strip_common_indent(programlisting: ET.Element):
    # Strip common indent
    commonIndent = 100000
    for line in programlisting:
        indent, empty = findIndent(line)
        if not empty:
            commonIndent = min(indent, commonIndent)

    for line in programlisting:
        indent = 0
        for e in line.iter():
            if indent < commonIndent and e.tag == "sp":
                indent += 1
                e.tag = "dummy"


def programlisting(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    # can add class linenums here if needed
    strip_common_indent(n)
    buffer.open("code", {"class": "prettyprint"})

    for line in n:
        ''' \todo ID '''
        # print(line)
        builder.layout.markup(ctx, line, buffer)
        buffer.voidelem("br")

    buffer.close("code")


# Used for deleted elements
def dummy(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass


def video(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    attrs = n.attrib
    buffer.open("video", params=attrs)

    # Rewrite the src attribute of the 'source' tag
    # to make sure it is correct even for nested pages
    for child in n:
        if child.tag == "source":
            childAttrs = dict(child.attrib)
            if "src" in childAttrs:
                childAttrs["src"] = ctx.relpath(childAttrs["src"])
            buffer.element("source", "", params=childAttrs)
        else:
            buffer.html(element_to_string(child))

        buffer.html(child.tail or "")
    buffer.close("video")


def element_to_string(element: ET.Element) -> str:
    return "".join(["" if element.text is None else element.text] + [ET.tostring(e, encoding="unicode", method="html") for e in element.getchildren()])


def verbatim(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer.html(element_to_string(n))


def indexentry(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass


def orderedlist(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer.open("ol")
    _doclist(ctx, n, buffer)
    buffer.close("ol")


def itemizedlist(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer.open("ul")
    _doclist(ctx, n, buffer)
    buffer.close("ul")


def _doclist(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    # Guaranteed to only contain listitem nodes
    for child in n:
        assert child.tag == "listitem"

        buffer.open("li")
        builder.layout.markup(ctx, child, buffer)
        buffer.close("li")


def simplesect(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    with buffer.outside_paragraph():
        kind = n.get("kind")
        title = n.find("title")
        buffer.open("div", {"class": "simplesect simplesect-" + kind})

        buffer.open("h3")
        if title is not None:
            builder.layout.markup(ctx, title, buffer)
        else:
            buffer += kind.title()

        buffer.close("h3")
        builder.layout.sectbase(ctx, n, buffer)
        buffer.close("div")


def simplesectsep(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass


def parameterlist(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    ''' Parameter lists have been collected and stored in a more object oriented manner'''
    pass


def title(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    raise Exception("Title tags should have been handled")


def anchor(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    builder.layout.ref(ctx, n, buffer)


def variablelist(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    entries = n.findall("varlistentry")
    items = n.findall("listitem")
    assert len(entries) == len(items)

    buffer.open("ul")

    for i in range(0, len(entries)):
        entry = entries[i]
        item = items[i]
        term = entry.find("term")
        # id = term.find("anchor").get("id")
        # refobj = term.find("ref")

        assert term is not None
        buffer.open("li")
        buffer.element("h4", lambda: builder.layout.markup(ctx, term, buffer))
        builder.layout.markup(ctx, item, buffer)
        buffer.close("li")

    buffer.close("ul")


def table(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer.open("table", params={"class": "table table-striped table-filled"})
    for row in n:
        buffer.open("tr", params=n.attrib)
        for cell in row:
            th = cell.get("thead") == "yes" or cell.tag == "th"
            buffer.open("th" if th else "td", params=cell.attrib)
            builder.layout.markup(ctx, cell, buffer)
            buffer.close("th" if th else "td")
        buffer.close("tr")
    buffer.close("table")


def copydetailed(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    name = n.get("name").replace("::",".")
    copy_candidates = []
    for entity in ctx.state.entities:
        name_suffix = ""
        c = entity
        while c is not None:
            name_suffix = c.name + "." + name_suffix if name_suffix != "" else c.name
            c = c.parent_in_canonical_path()
            if name_suffix == name:
                copy_candidates.append(entity)
                break

    if len(copy_candidates) == 0:
        print("Could not find any entity with the name '" + name + "' (used in a copydetailed tag).")
    elif len(copy_candidates) > 1:
        print("Ambigious reference '" + name + "' in a copydetailed tag. " + str((len(copy_candidates))) + " entities match this name.")
    else:
        builder.layout.markup(ctx, copy_candidates[0].detaileddescription, buffer)


def heading(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer.open("h" + n.get("level"))
    builder.layout.markup(ctx, n, buffer)
    buffer.close("h" + n.get("level"))


def get_image_variants(ctx: WritingContext, path: str) -> List[str]:
    root, ext = os.path.splitext(path)
    res = []
    for s in [(1, ""), (1, "@1x"), (1.5, "@1.5x"), (2, "@2x"), (3, "@3x"), (4, "@4x")]:
        local_path = root + s[1] + ext
        full_path = os.path.join(ctx.settings.out_dir, local_path)
        if os.path.isfile(full_path):
            # Found an image variant
            res.append((s[0], local_path))

    return res


def srcset2str(srcset: List[Tuple[int,str]]) -> str:
    return ",\n".join(path + " " + str(scale) + "x" for scale, path in srcset)


def image(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    src = n.get("src")
    if src is None:
        src = "images/" + n.get("name")

    srcset = get_image_variants(ctx, src)
    # Convert to relative paths
    srcset = [(s, ctx.relpath(p)) for s,p in srcset]
    scale1 = [p for s,p in srcset if s == 1]
    if len(srcset) == 0:
        print("Could not find image " + src)
        url = ctx.relpath(src)
    elif len(scale1) == 0:
        print("Image " + src + " does not have any variants with a scale of 1x")
        url = ctx.relpath(src)
    else:
        url = scale1[0]
        # the src attribute acts as a 1x image in the srcset
        srcset = [(s, p) for s,p in srcset if s != 1]

    buffer.open("div", {"class": "tinyshadow"})
    buffer.open("img", {"src": url, "srcset": srcset2str(srcset)})
    builder.layout.markup(ctx, n, buffer)
    buffer.close("img")
    buffer.close("div")


def dotfile(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass


def toclist(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass


def xrefsect(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    with buffer.outside_paragraph():
        title = n.find("xreftitle")
        desc = n.find("xrefdescription")
        id = n.get("id")

        # This is based on how Doxygen generates the id, which looks (for example) like
        # deprecated_1_deprecated000018
        # This will extract 'deprecated' as the key
        assert("_" in id)
        assert(title is not None)
        key = id.split("_")[0]

        buffer.open("div", {"class": "simplesect simplesect-" + key})

        buffer.open("h3")
        builder.layout.markup(ctx, title, buffer)
        buffer.close("h3")
        builder.layout.sectbase(ctx, desc, buffer)
        buffer.close("div")


def copydoc(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass


def blockquote(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass

##########################
# docTitleCmdGroup #######
##########################


def ulink(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer.element("a href='" + n.get("url") + "'", lambda: builder.layout.markup(ctx, n, buffer))


def bold(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer.element("b", lambda: builder.layout.markup(ctx, n, buffer))


def emphasis(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    bold(ctx, n, buffer)


def computeroutput(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    preformatted(ctx, n, buffer)


def subscript(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass


def superscript(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass


def center(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer.element("center", lambda: builder.layout.markup(ctx, n, buffer))


def small(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer.element("small", lambda: builder.layout.markup(ctx, n, buffer))


def htmlonly(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    verbatim(ctx, n, buffer)


# These should be pass only functions actually


def manonly(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass


def xmlonly(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass


def rtfonly(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass


def latexonly(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass


# May look similar to mdash in a monospace font, but it is not
def ndash(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer += "–"


def mdash(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer += "—"


# ...


def ref(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    builder.layout.ref(ctx, n, buffer)

##########################
# docTitleCmdGroup #######
##########################


def para(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer.element("p", lambda: builder.layout.markup(ctx, n, buffer))


def sp(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer += " "


def highlight(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    builder.layout.markup(ctx, n, buffer)


def innerpage(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    entity = ctx.getref(n)
    if entity is None:
        buffer.append(str(n.get("refid")))
    else:
        builder.layout.ref_entity(ctx, entity, buffer)


def render_template(ctx: WritingContext, template_name: str, **kwargs) -> str:
    template = ctx.jinja_environment.get_template(template_name + ".html")
    return template.render(
        page=ctx.page,
        state=ctx.state,
        relpath=ctx.relpath,
        sorted=ctx.sort_entities,
        getref=ctx.getref,
        **kwargs,
    )


def inspectorfield(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    title = n.get("title")
    entity = ctx.state.get_entity_by_path(n.get("refname"))

    primary_type = None
    if entity.type is not None:
        for n in entity.type:
            if n.tag == "ref":
                primary_type = ctx.getref(n)
    buffer.html(render_template(ctx, "inspectorfield", title=title, member=entity, primary_type=primary_type))


xml_mapping = {
    "linebreak": linebreak,
    "hruler": hruler,
    "preformatted": preformatted,
    "programlisting": programlisting,
    "verbatim": verbatim,
    "indexentry": indexentry,
    "orderedlist": orderedlist,
    "itemizedlist": itemizedlist,
    "simplesect": simplesect,
    "simplesectsep": simplesectsep,
    "parameterlist": parameterlist,
    "title": title,
    "anchor": anchor,
    "variablelist": variablelist,
    "table": table,
    "heading": heading,
    "image": image,
    "dotfile": dotfile,
    "toclist": toclist,
    "xrefsect": xrefsect,
    "copydoc": copydoc,
    "blockquote": blockquote,
    "ulink": ulink,
    "bold": bold,
    "emphasis": emphasis,
    "computeroutput": computeroutput,
    "subscript": subscript,
    "superscript": superscript,
    "center": center,
    "small": small,
    "htmlonly": htmlonly,
    "manonly": manonly,
    "xmlonly": xmlonly,
    "rtfonly": rtfonly,
    "latexonly": latexonly,
    "ndash": ndash,
    "mdash": mdash,
    "ref": ref,
    "para": para,
    "sp": sp,
    "highlight": highlight,
    "dummy": dummy,
    "video": video,
    "order": dummy,
    "copydetailed": copydetailed,
    "innerpage": innerpage,
    "inspectorfield": inspectorfield,
}


def write_xml(ctx, node, buffer) -> None:
    f = xml_mapping.get(node.tag)
    if f is not None:
        f(ctx, node, buffer)
    else:
        print("Not handled: " + node.tag)
