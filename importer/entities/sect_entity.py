from .entity import Entity
from typing import Dict
import xml.etree.ElementTree as ET
from importer.importer_context import ImporterContext


class SectEntity(Entity):
    def read_from_xml(self, ctx: ImporterContext) -> None:
        title = self.xml.find("title")
        self.name = Entity.formatname(str(title.text))
