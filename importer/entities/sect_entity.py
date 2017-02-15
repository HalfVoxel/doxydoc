from .entity import Entity
from typing import Dict
import xml.etree.ElementTree as ET


class SectEntity(Entity):
    def read_from_xml(self, xml2entity: Dict[ET.Element, Entity]) -> None:
        title = self.xml.find("title")
        self.name = Entity.formatname(str(title.text))
