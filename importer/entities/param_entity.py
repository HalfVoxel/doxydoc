from .entity import Entity
from typing import Optional
import xml.etree.ElementTree as ET
from importer.importer_context import ImporterContext


class ParamEntity(Entity):
    def __init__(self) -> None:
        super().__init__()

        self.type = None  # type: Optional[ET.Element]
        self.default_name = None  # type: Optional[ET.Element]

    def read_from_xml(self, ctx: ImporterContext) -> None:
        xml = self.xml
        assert xml is not None

        self.name = str(xml.find("declname").text)
        self.type = xml.find("type")
        self.default_value = xml.find("defval")
