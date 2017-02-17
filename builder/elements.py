# coding=UTF-8

from .str_tree import StrTree
import builder.layout
import xml.etree.ElementTree as ET
from .writing_context import WritingContext


def linebreak(ctx, n, buffer) -> None:
    buffer.elem("br")


def hruler(ctx, n, buffer) -> None:
    pass


def preformatted(ctx, n, buffer) -> None:
    buffer.element("pre", n.text)


def programlisting(ctx, n, buffer) -> None:
    # can add class linenums here if needed
    buffer.element("code", None, {"class": "prettyprint"})
    for line in n:
        ''' \todo ID '''
        builder.layout.markup(ctx, line, buffer)
        buffer.element("br")

    buffer.element("/code")


def verbatim(ctx, n, buffer) -> None:
    buffer.html(n.text)


def indexentry(ctx, n, buffer) -> None:
    pass


def orderedlist(ctx, n, buffer) -> None:
    buffer.element("ol", _doclist(ctx, n, buffer))


def itemizedlist(ctx, n, buffer) -> None:
    buffer.element("ul", _doclist(ctx, n, buffer))


def _doclist(ctx, n, buffer) -> None:
    # Guaranteed to only contain listitem nodes
    for child in n:
        assert child.tag == "listitem"

        buffer.elem("li")
        builder.layout.markup(ctx, child, buffer)
        buffer.elem("/li")


def simplesect(ctx, n, buffer) -> None:
    kind = n.get("kind")
    title = n.find("title")
    buffer.element("div", None, {"class": "simplesect simplesect-" + kind})

    buffer.element("h3")
    if title is not None:
        builder.layout.markup(ctx, title, buffer)
    else:
        buffer += kind.title()

    buffer.element("/h3")
    builder.layout.sectbase(ctx, n, buffer)
    buffer.element("/div")


def simplesectsep(ctx, n, buffer) -> None:
    pass


def parameterlist(ctx, n, buffer) -> None:
    ''' Parameter lists have been collected and stored in a more object oriented manner'''
    pass


def title(ctx, n, buffer) -> None:
    raise Exception("Title tags should have been handled")


def anchor(ctx, n, buffer) -> None:
    builder.layout.ref(ctx, n, buffer)


def variablelist(ctx: WritingContext, n: ET.Element, buffer: StrTree) -> None:
    entries = n.findall("varlistentry")
    items = n.findall("listitem")
    assert len(entries) == len(items)

    buffer.elem("ul")

    for i in range(0, len(entries)):
        entry = entries[i]
        item = items[i]
        term = entry.find("term")
        # id = term.find("anchor").get("id")
        # refobj = term.find("ref")

        assert term is not None
        buffer.elem("li")
        buffer.element("h4", lambda: builder.layout.markup(ctx, term, buffer))
        builder.layout.markup(ctx, item, buffer)
        buffer.elem("/li")

    buffer.elem("/ul")


def table(ctx, n, buffer) -> None:
    buffer.element("table")
    for row in n:
        buffer.element("tr")
        for cell in row:
            th = cell.get("thead") == "yes"
            buffer.element("th" if th else "td")
            builder.layout.markup(ctx, cell, buffer)
            buffer.element("/th" if th else "/td")
        buffer.element("/tr")
    buffer.element("/table")


def heading(ctx, n, buffer) -> None:
    pass


def image(ctx, n, buffer) -> None:
    url = ctx.relpath("images/" + n.get("name"))
    buffer.element("div", None, {"class": "tinyshadow"})
    buffer.element("img", None, {"src": url})
    builder.layout.markup(ctx, n, buffer)
    buffer.element("/img")
    buffer.element("/div")


def dotfile(ctx, n, buffer) -> None:
    pass


def toclist(ctx, n, buffer) -> None:
    pass


def xrefsect(ctx, n, buffer) -> None:
    pass


def copydoc(ctx, n, buffer) -> None:
    pass


def blockquote(ctx, n, buffer) -> None:
    pass

##########################
# docTitleCmdGroup #######
##########################


def ulink(ctx, n, buffer) -> None:
    buffer.element("a href='" + n.get("url") + "'", lambda: builder.layout.markup(ctx, n, buffer))


def bold(ctx, n, buffer) -> None:
    buffer.element("b", lambda: builder.layout.markup(ctx, n, buffer))


def emphasis(ctx, n, buffer) -> None:
    bold(ctx, n, buffer)


def computeroutput(ctx, n, buffer) -> None:
    preformatted(ctx, n, buffer)


def subscript(ctx, n, buffer) -> None:
    pass


def superscript(ctx, n, buffer) -> None:
    pass


def center(ctx, n, buffer) -> None:
    buffer.element("center", lambda: builder.layout.markup(ctx, n, buffer))


def small(ctx, n, buffer) -> None:
    buffer.element("small", lambda: builder.layout.markup(ctx, n, buffer))


def htmlonly(ctx, n, buffer) -> None:
    verbatim(ctx, n, buffer)


# These should be pass only functions actually


def manonly(ctx, n, buffer) -> None:
    pass


def xmlonly(ctx, n, buffer) -> None:
    pass


def rtfonly(ctx, n, buffer) -> None:
    pass


def latexonly(ctx, n, buffer) -> None:
    pass


# May look similar to mdash in a monospace font, but it is not
def ndash(ctx, n, buffer) -> None:
    buffer += "–"


def mdash(ctx, n, buffer) -> None:
    buffer += "—"


# ...


def ref(ctx, n, buffer) -> None:
    builder.layout.ref(ctx, n, buffer)

##########################
# docTitleCmdGroup #######
##########################


def para(ctx, n, buffer) -> None:
    buffer.element("p", lambda: builder.layout.markup(ctx, n, buffer))


def sp(ctx, n, buffer) -> None:
    buffer += " "


def highlight(ctx, n, buffer) -> None:
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
