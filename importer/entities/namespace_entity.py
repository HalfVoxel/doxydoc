from .entity import Entity, gather_members
from typing import Dict
import xml.etree.ElementTree as ET


class NamespaceEntity(Entity):
    def __init__(self):
        super().__init__()

        self.innerclasses = []
        self.innernamespaces = []

        self.parent_namespace = None

    def parent_in_canonical_path(self):
        return self.parent_namespace

    def read_from_xml(self, xml2entity: Dict[ET.Element, Entity]) -> None:
        super().read_from_xml(xml2entity)
        xml = self.xml

        self.innerclasses = [node.get("ref") for node in xml.findall("innerclass")]
        self.innernamespaces = [node.get("ref") for node in xml.findall("innernamespaces")]

        for innerclass in self.innerclasses:
            innerclass.parent = self

        for innernamespace in self.innernamespaces:
            innernamespace.parent_namespace = self

        self.members = gather_members(xml)
