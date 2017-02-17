# coding=UTF-8

from .str_tree import StrTree
import builder.layout
import xml.etree.ElementTree as ET
from .writing_context import WritingContext


def linebreak(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer.voidelem("br")


def hruler(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass


def preformatted(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer.element("pre", n.text)


def programlisting(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    # can add class linenums here if needed
    buffer.open("code", {"class": "prettyprint"})
    for line in n:
        ''' \todo ID '''
        builder.layout.markup(ctx, line, buffer)
        buffer.voidelem("br")

    buffer.close("code")


def verbatim(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    buffer.html(str(n.text))


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
    buffer.open("table")
    for row in n:
        buffer.open("tr")
        for cell in row:
            th = cell.get("thead") == "yes"
            buffer.open("th" if th else "td")
            builder.layout.markup(ctx, cell, buffer)
            buffer.close("th" if th else "td")
        buffer.close("tr")
    buffer.close("table")


def heading(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    pass


def image(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    url = ctx.relpath("images/" + n.get("name"))
    buffer.open("div", {"class": "tinyshadow"})
    buffer.open("img", {"src": url})
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
    "highlight": highlight
}


def write_xml(ctx, node, buffer) -> None:
    f = xml_mapping.get(node.tag)
    if f is not None:
        f(ctx, node, buffer)
    else:
        print("Not handled: " + node.tag)
