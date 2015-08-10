# coding=UTF-8

from doxybase import DocState, JinjaFilter
from str_tree import StrTree
import doxylayout


def linebreak(n):
    return StrTree().elem("br")


def hruler(n):
    return StrTree()


def preformatted(n):
    return StrTree().element("pre", n.text)


@JinjaFilter
def programlisting(n):
    # can add class linenums here if needed
    result = StrTree()
    result.element("code", None, {"class": "prettyprint"})
    for line in n:
        ''' \todo ID '''
        result += doxylayout.markup(line)
        result.element("br")

    result.element("/code")
    return result


def verbatim(n):
    return StrTree().html(n.text)


def indexentry(n):
    return StrTree()


def orderedlist(n):
    return StrTree().element("ol", _doclist(n))


def itemizedlist(n):
    return StrTree().element("ul", _doclist(n))


def _doclist(n):
    # Guaranteed to only contain listitem nodes
    result = StrTree()
    for child in n:
        assert child.tag == "listitem"

        result.elem("li")
        result += doxylayout.markup(child)
        result.elem("/li")

    return result


def simplesect(n):
    result = StrTree()
    kind = n.get("kind")
    title = n.find("title")
    result.element("div", None, {"class": "simplesect simplesect-" + kind})

    result.element("h3")
    if title is not None:
        result += doxylayout.markup(title)
    else:
        result += kind.title()

    result.element("/h3")
    result += doxylayout.sectbase(n)
    result.element("/div")
    return result


def simplesectsep(n):
    return StrTree()


def parameterlist(n):
    ''' Parameter lists have been collected and stored in a more object oriented manner'''
    return StrTree()


def title(n):
    raise "Title tags should have been handled"


def anchor(n):
    return doxylayout.ref(n)


def variablelist(n):
    entries = n.findall("varlistentry")
    items = n.findall("listitem")
    assert len(entries) == len(items)

    result = StrTree()
    result.elem("ul")

    for i in xrange(0, len(entries)):
        entry = entries[i]
        item = items[i]
        term = entry.find("term")
        # id = term.find("anchor").get("id")
        # refobj = term.find("ref")

        assert term is not None, DocState.currentobj
        result.elem("li")
        result.element("h4", lambda: doxylayout.markup(term))
        result += doxylayout.markup(item)
        result.elem("/li")

    result.elem("/ul")
    return result


def table(n):
    result = StrTree()
    result.element("table")
    for row in n:
        result.element("tr")
        for cell in row:
            th = cell.get("thead") == "yes"
            result.element("th" if th else "td")
            result += doxylayout.markup(cell)
            result.element("/th" if th else "/td")
        result.element("/tr")
    result.element("/table")
    return result


def heading(n):
    return StrTree()


def image(n):
    result = StrTree()
    name = "images/" + n.get("name")
    result.element("div", None, {"class": "tinyshadow"})
    result.element("img", None, {"src": name})
    result += doxylayout.markup(n)
    result.element("/img")
    result.element("/div")
    return result


def dotfile(n):
    return StrTree()


def toclist(n):
    return StrTree()


def xrefsect(n):
    return StrTree()


def copydoc(n):
    return StrTree()


def blockquote(n):
    return StrTree()

##########################
# docTitleCmdGroup #######
##########################


def ulink(n):
    return StrTree().element("a href='" + n.get("url") + "'", doxylayout.markup(n))


def bold(n):
    return StrTree().element("b", doxylayout.markup(n))


def emphasis(n):
    return bold(n)


def computeroutput(n):
    return preformatted(n)


def subscript(n):
    return StrTree()


def superscript(n):
    return StrTree()


def center(n):
    return StrTree().element("center", doxylayout.markup(n))


def small(n):
    return StrTree().element("small", doxylayout.markup(n))


def htmlonly(n):
    return verbatim(n)


# These should be pass only functions actually


def manonly(n):
    return StrTree()


def xmlonly(n):
    return StrTree()


def rtfonly(n):
    return StrTree()


def latexonly(n):
    return StrTree()


# May look similar to mdash in a monospace font, but it is not
def ndash(n):
    return StrTree("–")


def mdash(n):
    return StrTree("—")


# ...


def ref(n):
    return doxylayout.ref(n)

##########################
# docTitleCmdGroup #######
##########################


def para(n):
    return StrTree().element("p", doxylayout.markup(n))


def sp(n):
    return StrTree(" ")


def highlight(n):
    return doxylayout.markup(n)


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


def write_xml(node):
    f = xml_mapping.get(node.tag)
    return f(node) if f is not None else StrTree()
