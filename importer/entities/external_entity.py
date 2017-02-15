from .entity import Entity
from typing import Dict
import xml.etree.ElementTree as ET


class ExternalEntity(Entity):
    def read_from_xml(self, xml2entity: Dict[ET.Element, Entity]) -> None:
        # Nothing to read since this
        # entity is not based on an XML file
        pass
