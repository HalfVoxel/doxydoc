from .entity import Entity, gather_members
from importer.protection import Protection
from typing import Dict
import xml.etree.ElementTree as ET


class ClassEntity(Entity):
    def __init__(self):
        super().__init__()

        self.protection = Protection()
        self.inherits_from = []
        self.derived = []
        self.members = []
        self.all_members = []
        self.inner_classes = []

        # Namespace or class parent
        # If class, this is an inner class
        self.parent = None

    # Parent in canonical path
    # if this is
    # A::B::C
    # Then the class C has the namespace B as parent
    # and Bs parent is A.
    # A has None as the parent.
    def parent_in_canonical_path(self):
        return self.parent

    def read_from_xml(self, xml2entity: Dict[ET.Element, Entity]) -> None:
        super().read_from_xml(xml2entity)
        xml = self.xml

        self.protection = xml.get("prot")
        self.members = gather_members(xml)

        self.briefdescription = xml.find("briefdescription")
        self.detaileddescription = xml.find("detaileddescription")

        self.final = xml.get("final") == "yes"
        self.sealed = xml.get("sealed") == "yes"
        self.abstract = xml.get("abstract") == "yes"

        self.inherits_from = [node.get("ref") for node in xml.findall("basecompoundref")]
        self.derived = [node.get("ref") for node in xml.findall("derivedcompoundref")]

        self.inner_classes = [node.get("ref") for node in xml.findall("innerclass")]
        for inner_class in self.inner_classes:
            inner_class.parent = self

        # All members, also inherited ones
        self.all_members = [m.get("ref") for m in xml.find("listofallmembers")]
        for m in xml.find("listofallmembers"):
            if m.get("ref") is None:
                print ("NULL REFERENCE " + m.find("name").text + " " + m.find("scope").text)
                print ("Sure not old files are in the xml directory")
