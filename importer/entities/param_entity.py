from .entity import Entity
from typing import Dict
import xml.etree.ElementTree as ET
from importer.importer_context import ImporterContext


class ParamEntity(Entity):
    def __init__(self) -> None:
        super().__init__()

        self.type = None  # type: ET.Element

    def read_from_xml(self, ctx: ImporterContext) -> None:
        xml = self.xml

        self.name = str(xml.find("declname").text)
        self.type = xml.find("type")
