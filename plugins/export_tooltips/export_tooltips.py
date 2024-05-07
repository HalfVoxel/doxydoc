import os
from typing import cast
from builder.builder import Builder
from builder.layout import description
from builder.str_tree import StrTree
from builder.writing_context import WritingContext
from doxydoc_plugin import DoxydocPlugin
from importer.entities.entity import Entity
from importer.entities.member_entity import MemberEntity
from importer.importer_context import ImporterContext
import xml.etree.ElementTree as ET

class Plugin(DoxydocPlugin):
    output_path: str | None

    def __init__(self, config):
        super().__init__(config)
        self.output_path = config["output_path"] if config is not None else None


    def on_post_build_html(self, importer: ImporterContext, builder: Builder, entity2page):
        if self.output_path is None:
            print("No output path specified for tooltips. Skipping.")
            return
        ctx = cast(ImporterContext, importer.ctx)
        entities = cast(list[Entity], importer.entities)
        output = []
        seen = set()
        for entity in entities:
            if isinstance(entity, MemberEntity) and entity.kind != "function":
                path = entity.full_canonical_path(".")
                buffer = StrTree()
                buffer2 = StrTree()
                # _tooltip(builder.default_writing_context, entity, buffer)
                writing_ctx = builder.default_writing_context.with_link_stripping()
                writing_ctx.relpath = lambda x: "no path"
                writing_ctx.entity_scope = entity
                writing_ctx.page = None
                if entity.briefdescription is not None:
                    description(writing_ctx, entity.briefdescription, buffer)
                if entity.detaileddescription is not None:
                    description(writing_ctx, entity.detaileddescription, buffer2)
                
                source = str(buffer) + "\n\n" + str(buffer2)
                source = source.replace("<br>", "<br />")
                try:
                    tree = ET.fromstring("<span>" + source + "</span>")
                except Exception as e:
                    raise Exception("Failed to parse XML for " + path + "\n\n'" + source + "'") from e
                for item in tree.iter():
                    if item.tag == "p":
                        item.tag = "span"
                        if item.tail is None:
                            item.tail = ""
                        item.tail += "\n\n"
                    elif item.tag in ["a", "i", "b", "span", "br"]:
                        pass
                    elif item.tag in ["code"]:
                        item.tag = "b"
                        item.clear()
                        item.text = "[code in online documentation]"
                    elif item.tag in ["img"]:
                        item.tag = "b"
                        item.clear()
                        item.text = "[image in online documentation]"
                    elif item.tag in ["ul"]:
                        item.tag = "span"
                        item.text = "\n" + (item.text if item.text is not None else "")
                        if item.tail is None:
                            item.tail = ""
                        item.tail += "\n"
                    elif item.tag in ["li"]:
                        item.tag = "span"
                        item.text = "- " + (item.text if item.text is not None else "")
                        if item.tail is None:
                            item.tail = ""
                        item.tail += "\n"
                    elif item.tag in ["video", "iframe"]:
                        item.tag = "b"
                        item.clear()
                        item.text = "[video in online documentation]"
                    elif item.tag in ["div", "table", "tr", "td", "th", "tbody", "thead", "tfoot", "colgroup", "col", "caption"]:
                        item.tag = "span"
                        item.clear()
                        item.text = "[more in online documentation]"
                    else:
                        raise Exception("Unknown tag: " + item.tag)
                
                s = ET.tostring(tree, encoding="unicode")
                s = s.replace("<span>", "").replace("</span>", "").replace("<span />", "")
                s = s.replace("<br/>", "\n").replace("<br />", "\n")
                for _ in range(3):
                    s = s.replace("\n\n\n", "\n\n")
                for p in ["[more in online documentation]", "[image in online documentation]", "[code in online documentation]", "[video in online documentation]"]:
                    while p + "\n\n" + p in s:
                        s = s.replace(p + "\n\n" + p, p + "\n\n")
                s = s.strip()
                s = s.replace("\n", "\\n")
                if path not in seen:
                    seen.add(path)
                    output.append(path + "\t" + entity.path.full_url() + "\t" + s)
            
        output.sort()
        with open(os.path.join(builder.settings.out_dir, self.output_path), "w") as f:
            f.write("\n".join(output))

