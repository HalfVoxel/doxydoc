from os import listdir
import xml.etree.ElementTree as ET
from os.path import isfile, isdir, join
from importer import Importer
from importer.entities import ExternalEntity, Entity, ClassEntity, PageEntity, NamespaceEntity, ExampleEntity, GroupEntity, MemberEntity
import os
import json
from typing import Any, List, Dict
import argparse
import builder.settings
from builder.str_tree import StrTree
from builder.elements import strip_common_indent

class XMLCommentConverter:
    def find_xml_files(self, path: str) -> List[str]:
        return [join(path, f) for f in listdir(path)
                if isfile(join(path, f)) and f.endswith(".xml")]

    def __init__(self):
        self.settings = None  # type: builder.settings.Settings
        self.importer = Importer()

    def run_interative(self):
        parser = argparse.ArgumentParser(description='Generate HTML from Doxygen\'s XML output')
        parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
        parser.add_argument("-q", "--quiet", help="Quiet output", action="store_true")
        parser.add_argument("-c", "--config", default="config.json", help="Path to config file", type=str)

        args = parser.parse_args()
        try:
            config = json.loads(open(args.config).read())
        except Exception as e:
            print("Could not read configuration at '" + args.config + "'\n" + str(e))
            exit(1)

        self.generate(config)

    def generate(self, config):
        self.settings = builder.settings.Settings(config)
        self.importer.read(self.find_xml_files(os.path.join(self.settings.in_dir, "xml")))

        bld = Builder()

        for entity in self.importer.entities:
            if isinstance(entity, MemberEntity) or isinstance(entity, ClassEntity) or isinstance(entity, NamespaceEntity):
                print("------")
                ctx = WritingContext(self.importer)
                buffer = StrTree(escape_html=False)

                if entity.briefdescription is not None:
                    bld.markup(ctx, entity.briefdescription, buffer)
                if entity.detaileddescription is not None:
                    bld.markup(ctx, entity.detaileddescription, buffer)
                print(process_comment(str(buffer)))
                print("------")


def remove_duplicate_empty_lines(lines: List[str]) -> List[str]:
    new_lines = []
    for line in lines:
        if line == "" and (len(new_lines) != 0 and new_lines[-1] == ""):
            continue

        new_lines.append(line)
    return new_lines


def process_comment(text: str) -> str:
    lines = [l for l in text.split('\n')]
    lines = remove_duplicate_empty_lines(lines)
    return "\n".join(lines).strip()


class WritingContext:
    def __init__(self, state: Importer):
        self.state = state
        self.strip_links = False

    def with_link_stripping(self) -> 'WritingContext':
        ret = WritingContext(self.state)
        ret.strip_links = True
        return ret


def element_to_string(element: ET.Element) -> str:
    return "".join(["" if element.text is None else element.text] + [ET.tostring(e, encoding="unicode", method="html") for e in element.getchildren()])


class Builder:
    def __init__(self):
        self.xml_mapping = {
            "linebreak": self.linebreak,
            "hruler": self.hruler,
            "preformatted": self.preformatted,
            "programlisting": self.programlisting,
            "verbatim": self.verbatim,
            "indexentry": self.indexentry,
            "orderedlist": self.orderedlist,
            "itemizedlist": self.itemizedlist,
            "simplesect": self.simplesect,
            "simplesectsep": self.simplesectsep,
            "parameterlist": self.parameterlist,
            "title": self.title,
            "anchor": self.anchor,
            "variablelist": self.variablelist,
            "table": self.table,
            "heading": self.heading,
            "image": self.image,
            "dotfile": self.dotfile,
            "toclist": self.toclist,
            "xrefsect": self.xrefsect,
            "copydoc": self.copydoc,
            "blockquote": self.blockquote,
            "ulink": self.ulink,
            "bold": self.bold,
            "emphasis": self.emphasis,
            "computeroutput": self.computeroutput,
            "subscript": self.subscript,
            "superscript": self.superscript,
            "center": self.center,
            "small": self.small,
            "htmlonly": self.htmlonly,
            "manonly": self.manonly,
            "xmlonly": self.xmlonly,
            "rtfonly": self.rtfonly,
            "latexonly": self.latexonly,
            "ndash": self.ndash,
            "mdash": self.mdash,
            "ref": self.ref,
            "para": self.para,
            "sp": self.sp,
            "highlight": self.highlight,
            "dummy": self.dummy,
            "video": self.video,
            "order": self.dummy,
            "copydetailed": self.copydetailed,
            "innerpage": self.innerpage,
            "inspectorfield": self.inspectorfield,
        }

    def markup(self, ctx: WritingContext, node: ET.Element, buffer: StrTree) -> None:
        ''' Markup like nodes '''

        if node is None:
            return

        if node.text is not None:
            buffer += node.text

        # Traverse children
        for n in node:
            # buffer += "<" + n.tag + ">"
            self.write_xml(ctx, n, buffer)

            if n.tail is not None:
                buffer += n.tail

    def write_xml(self, ctx: WritingContext, node: ET.Element, buffer: StrTree) -> None:
        self.ctx = ctx
        f = self.xml_mapping.get(node.tag)
        if f is not None:
            f(ctx, node, buffer)
        else:
            print("Not handled: " + node.tag)

    def linebreak(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        buffer += '\n'

    def hruler(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        buffer.html('-----------')

    def preformatted(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        buffer.html('\n' + node.text + '\n')

    def programlisting(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        strip_common_indent(node)
        ctx = ctx.with_link_stripping()

        nchildren = len(node)
        if nchildren <= 1:
            buffer += "<c>"
            for line in node:
                self.markup(ctx, line, buffer)

            buffer += "</c>\n"
        else:
            buffer += '\n'
            buffer += "<code>"
            buffer += '\n'
            for line in node:
                self.markup(ctx, line, buffer)
                buffer += '\n'

            buffer += "</code>\n"

    def verbatim(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        buffer.html(element_to_string(node))

    def indexentry(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def orderedlist(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        for child in node:
            assert child.tag == "listitem"

            buffer.html("- ")
            self.markup(ctx, child, buffer)

    def itemizedlist(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        self.orderedlist(ctx, node, buffer)

    def simplesect(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def simplesectsep(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def parameterlist(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def title(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def anchor(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def variablelist(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def table(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def heading(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def image(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        buffer.html("[View in the online documentation to see images]")

    def dotfile(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def toclist(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def xrefsect(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def copydoc(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def blockquote(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def ulink(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def bold(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        buffer.html("*")
        self.markup(ctx, node, buffer)
        buffer.html("*")

    def emphasis(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        # buffer += "<paramref name=\""
        self.markup(ctx, node, buffer)
        # buffer += "\"/>"
        # self.bold(ctx, node, buffer)

    def computeroutput(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        return self.preformatted(ctx, node, buffer)

    def subscript(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        buffer.html("_")
        self.markup(ctx, node, buffer)

    def superscript(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        buffer.html("^")
        self.markup(ctx, node, buffer)

    def center(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        self.markup(ctx, node, buffer)

    def small(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        self.markup(ctx, node, buffer)

    def htmlonly(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        self.verbatim(ctx, node, buffer)

    def manonly(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def xmlonly(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        self.verbatim(ctx, node, buffer)

    def rtfonly(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def latexonly(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def ndash(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        buffer += "–"
        pass

    def mdash(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        buffer += "—"
        pass

    def ref(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        if ctx.strip_links:
            self.markup(ctx, node, buffer)
        else:
            obj = ctx.state.ctx.getref(node)
            if obj is None:
                self.markup(ctx, node, buffer)
            else:
                buffer.html(f'<see cref="{obj.full_canonical_path()}"/>')

    def para(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        buffer += "\n"
        self.markup(ctx, node, buffer)
        buffer += "\n"

    def sp(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        buffer += " "

    def highlight(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        self.markup(ctx, node, buffer)

    def dummy(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def video(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        buffer.html("[View in the online documentation to see videos]")

    def copydetailed(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def innerpage(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass

    def inspectorfield(self, ctx: WritingContext, node: ET.Element, buffer: StrTree):
        pass


XMLCommentConverter().run_interative()
