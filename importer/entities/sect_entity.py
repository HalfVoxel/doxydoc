from .entity import Entity
import xml.etree.ElementTree as ET
from importer.importer_context import ImporterContext
from typing import Optional


class SectEntity(Entity):
    def __init__(self) -> None:
        super().__init__()
        self.title: Optional[str] = None
        self.children: list[Entity] | None = None
        self.sect_level = -1

    def read_from_xml(self, ctx: ImporterContext) -> None:
        xml = self.xml
        assert(xml is not None)

        self.title = xml.find("title").text
        # Doxygen generates the ID as "pagename_1realname"
        # so we try to extract it here
        self.name_with_generics = self.name = self.id.split("_1")[-1]

        sect_level = int(self.xml.tag.replace("sect", ""))
        self.sect_level = sect_level
        children_tags = self.xml.findall(".//sect" + str(sect_level + 1))
        self.children = [ctx.getentity(x) for x in children_tags]
