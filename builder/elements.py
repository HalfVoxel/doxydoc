# coding=UTF-8

from .str_tree import StrTree
import builder.layout


def linebreak(ctx, n):
    return StrTree().elem("br")


def hruler(ctx, n):
    return StrTree()


def preformatted(ctx, n):
    return StrTree().element("pre", n.text)


def programlisting(ctx, n):
    # can add class linenums here if needed
    result = StrTree()
    result.element("code", None, {"class": "prettyprint"})
    for line in n:
        ''' \todo ID '''
        result += builder.layout.markup(ctx, line)
        result.element("br")

    result.element("/code")
    return result


def verbatim(ctx, n):
    return StrTree().html(n.text)


def indexentry(ctx, n):
    return StrTree()


def orderedlist(ctx, n):
    return StrTree().element("ol", _doclist(ctx, n))


def itemizedlist(ctx, n):
    return StrTree().element("ul", _doclist(ctx, n))


def _doclist(ctx, n):
    # Guaranteed to only contain listitem nodes
    result = StrTree()
    for child in n:
        assert child.tag == "listitem"

        result.elem("li")
        result += builder.layout.markup(ctx, child)
        result.elem("/li")

    return result


def simplesect(ctx, n):
    result = StrTree()
    kind = n.get("kind")
    title = n.find("title")
    result.element("div", None, {"class": "simplesect simplesect-" + kind})

    result.element("h3")
    if title is not None:
        result += builder.layout.markup(ctx, title)
    else:
        result += kind.title()

    result.element("/h3")
    result += builder.layout.sectbase(ctx, n)
    result.element("/div")
    return result


def simplesectsep(ctx, n):
    return StrTree()


def parameterlist(ctx, n):
    ''' Parameter lists have been collected and stored in a more object oriented manner'''
    return StrTree()


def title(ctx, n):
    raise Exception("Title tags should have been handled")


def anchor(ctx, n):
    return builder.layout.ref(ctx, n)


def variablelist(ctx, n):
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

        assert term is not None
        result.elem("li")
        result.element("h4", lambda: builder.layout.markup(ctx, term))
        result += builder.layout.markup(ctx, item)
        result.elem("/li")

    result.elem("/ul")
    return result


def table(ctx, n):
    result = StrTree()
    result.element("table")
    for row in n:
        result.element("tr")
        for cell in row:
            th = cell.get("thead") == "yes"
            result.element("th" if th else "td")
            result += builder.layout.markup(ctx, cell)
            result.element("/th" if th else "/td")
        result.element("/tr")
    result.element("/table")
    return result


def heading(ctx, n):
    return StrTree()


def image(ctx, n):
    result = StrTree()
    url = ctx.relpath("images/" + n.get("name"))
    result.element("div", None, {"class": "tinyshadow"})
    result.element("img", None, {"src": url})
    result += builder.layout.markup(ctx, n)
    result.element("/img")
    result.element("/div")
    return result


def dotfile(ctx, n):
    return StrTree()


def toclist(ctx, n):
    return StrTree()


def xrefsect(ctx, n):
    return StrTree()


def copydoc(ctx, n):
    return StrTree()


def blockquote(ctx, n):
    return StrTree()

##########################
# docTitleCmdGroup #######
##########################


def ulink(ctx, n):
    return StrTree().element("a href='" + n.get("url") + "'", builder.layout.markup(ctx, n))


def bold(ctx, n):
    return StrTree().element("b", builder.layout.markup(ctx, n))


def emphasis(ctx, n):
    return bold(ctx, n)


def computeroutput(ctx, n):
    return preformatted(ctx, n)


def subscript(ctx, n):
    return StrTree()


def superscript(ctx, n):
    return StrTree()


def center(ctx, n):
    return StrTree().element("center", builder.layout.markup(ctx, n))


def small(ctx, n):
    return StrTree().element("small", builder.layout.markup(ctx, n))


def htmlonly(ctx, n):
    return verbatim(ctx, n)


# These should be pass only functions actually


def manonly(ctx, n):
    return StrTree()


def xmlonly(ctx, n):
    return StrTree()


def rtfonly(ctx, n):
    return StrTree()


def latexonly(ctx, n):
    return StrTree()


# May look similar to mdash in a monospace font, but it is not
def ndash(ctx, n):
    return StrTree("–")


def mdash(ctx, n):
    return StrTree("—")


# ...


def ref(ctx, n):
    return builder.layout.ref(ctx, n)

##########################
# docTitleCmdGroup #######
##########################


def para(ctx, n):
    return StrTree().element("p", builder.layout.markup(ctx, n))


def sp(ctx, n):
    return StrTree(" ")


def highlight(ctx, n):
    return builder.layout.markup(ctx, n)


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


def write_xml(ctx, node):
    f = xml_mapping.get(node.tag)
    return f(ctx, node) if f is not None else StrTree()
