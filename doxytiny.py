# coding=UTF-8

from doxybase import DocState
from str_tree import StrTree
import doxylayout


def linebreak(n, ctx):
    return StrTree().elem("br")


def hruler(n, ctx):
    return StrTree()


def preformatted(n, ctx):
    return StrTree().element("pre", n.text)


def programlisting(n, ctx):
    # can add class linenums here if needed
    result = StrTree()
    result.element("code", None, {"class": "prettyprint"})
    for line in n:
        ''' \todo ID '''
        result += doxylayout.markup(line, ctx)
        result.element("br")

    result.element("/code")
    return result


def verbatim(n, ctx):
    return StrTree().html(n.text)


def indexentry(n, ctx):
    return StrTree()


def orderedlist(n, ctx):
    return StrTree().element("ol", _doclist(n, ctx))


def itemizedlist(n, ctx):
    return StrTree().element("ul", _doclist(n, ctx))


def _doclist(n, ctx):
    # Guaranteed to only contain listitem nodes
    result = StrTree()
    for child in n:
        assert child.tag == "listitem"

        result.elem("li")
        result += doxylayout.markup(child, ctx)
        result.elem("/li")

    return result


def simplesect(n, ctx):
    result = StrTree()
    kind = n.get("kind")
    title = n.find("title")
    result.element("div", None, {"class": "simplesect simplesect-" + kind})

    result.element("h3")
    if title is not None:
        result += doxylayout.markup(title, ctx)
    else:
        result += kind.title()

    result.element("/h3")
    result += doxylayout.sectbase(n, ctx)
    result.element("/div")
    return result


def simplesectsep(n, ctx):
    return StrTree()


def parameterlist(n, ctx):
    ''' Parameter lists have been collected and stored in a more object oriented manner'''
    return StrTree()


def title(n, ctx):
    raise "Title tags should have been handled"


def anchor(n, ctx):
    return doxylayout.ref(n, ctx)


def variablelist(n, ctx):
    entries = n.findall("varlistentry")
    items = n.findall("listitem")
    assert len(entries) == len(items)

    result = StrTree()
    result.elem("ul")

    for i in range(0, len(entries)):
        entry = entries[i]
        item = items[i]
        term = entry.find("term")
        # id = term.find("anchor").get("id")
        # refobj = term.find("ref")

        assert term is not None, DocState.currentobj
        result.elem("li")
        result.element("h4", lambda: doxylayout.markup(term, ctx))
        result += doxylayout.markup(item, ctx)
        result.elem("/li")

    result.elem("/ul")
    return result


def table(n, ctx):
    result = StrTree()
    result.element("table")
    for row in n:
        result.element("tr")
        for cell in row:
            th = cell.get("thead") == "yes"
            result.element("th" if th else "td")
            result += doxylayout.markup(cell, ctx)
            result.element("/th" if th else "/td")
        result.element("/tr")
    result.element("/table")
    return result


def heading(n, ctx):
    return StrTree()


def image(n, ctx):
    result = StrTree()
    name = "images/" + n.get("name")
    result.element("div", None, {"class": "tinyshadow"})
    result.element("img", None, {"src": name})
    result += doxylayout.markup(n, ctx)
    result.element("/img")
    result.element("/div")
    return result


def dotfile(n, ctx):
    return StrTree()


def toclist(n, ctx):
    return StrTree()


def xrefsect(n, ctx):
    return StrTree()


def copydoc(n, ctx):
    return StrTree()


def blockquote(n, ctx):
    return StrTree()

##########################
# docTitleCmdGroup #######
##########################


def ulink(n, ctx):
    return StrTree().element("a href='" + n.get("url") + "'", doxylayout.markup(n, ctx))


def bold(n, ctx):
    return StrTree().element("b", doxylayout.markup(n, ctx))


def emphasis(n, ctx):
    return bold(n, ctx)


def computeroutput(n, ctx):
    return preformatted(n, ctx)


def subscript(n, ctx):
    return StrTree()


def superscript(n, ctx):
    return StrTree()


def center(n, ctx):
    return StrTree().element("center", doxylayout.markup(n, ctx))


def small(n, ctx):
    return StrTree().element("small", doxylayout.markup(n, ctx))


def htmlonly(n, ctx):
    return verbatim(n, ctx)


# These should be pass only functions actually


def manonly(n, ctx):
    return StrTree()


def xmlonly(n, ctx):
    return StrTree()


def rtfonly(n, ctx):
    return StrTree()


def latexonly(n, ctx):
    return StrTree()


# May look similar to mdash in a monospace font, but it is not
def ndash(n, ctx):
    return StrTree("–")


def mdash(n, ctx):
    return StrTree("—")


# ...


def ref(n, ctx):
    return doxylayout.ref(n, ctx)

##########################
# docTitleCmdGroup #######
##########################


def para(n, ctx):
    return StrTree().element("p", doxylayout.markup(n, ctx))


def sp(n, ctx):
    return StrTree(" ")


def highlight(n, ctx):
    return doxylayout.markup(n, ctx)


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


def write_xml(node, ctx):
    f = xml_mapping.get(node.tag)
    return f(node, ctx) if f is not None else StrTree()
