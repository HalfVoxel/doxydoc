from .entity import Entity
from typing import Dict
import xml.etree.ElementTree as ET


class ParamEntity(Entity):
    def __init__(self):
        super().__init__()

        self.type = None  # type: ET.Element

    def read_from_xml(self, xml2entity: Dict[ET.Element, Entity]) -> None:
        xml = self.xml

        self.name = str(xml.find("declname").text)
        self.type = xml.find("type")
