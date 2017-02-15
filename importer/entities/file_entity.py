from .entity import Entity, gather_members
from typing import Dict
import xml.etree.ElementTree as ET


class FileEntity(Entity):
    def __init__(self):
        super().__init__()

        self.innerclasses = []
        self.innernamespaces = []
        self.contents = None
        self.location = None  # TODO: Unknown location
        # TODO gather_members

    def read_from_xml(self, xml2entity: Dict[ET.Element, Entity]) -> None:
        super().read_from_xml(xml2entity)
        xml = self.xml

        self.innerclasses = [node.get("ref") for node in xml.findall("innerclass")]
        self.innernamespaces = [node.get("ref") for node in xml.findall("innernamespace")]

        self.contents = xml.find("programlisting")

        self.members = gather_members(xml)
        # Only one members list
        self.all_members = self.members

        # Find location of file
        loc = xml.find("location")
        self.location = loc.get("file") if loc is not None else None
