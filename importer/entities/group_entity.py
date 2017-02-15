from .entity import Entity
from typing import Dict
import xml.etree.ElementTree as ET


class GroupEntity(Entity):
    def __init__(self):
        super().__init__()
        self.innerclasses = []
        self.innernamespaces = []
        self.innergroups = []

    def read_from_xml(self, xml2entity: Dict[ET.Element, Entity]) -> None:
        super().read_from_xml(xml2entity)
        xml = self.xml

        self.title = Entity.formatname(xml.find("title").text)

        self.innerclasses = [node.get("ref") for node in xml.findall("innerclass")]
        self.innernamespaces = [node.get("ref") for node in xml.findall("innernamespace")]

        self.innergroups = [node.get("ref") for node in xml.findall("innergroup")]
