from .entity import Entity, gather_members
from importer.protection import Protection
from typing import Dict
import xml.etree.ElementTree as ET
from importer.importer_context import ImporterContext


class Extends:
    def __init__(self, xml):
        self.virtual = None  # type: str
        self.protection = None  # type: str
        self.entity = None  # type: Entity
        # TODO: Can this be something more complicated than str? E.g if inheriting from a generic class?
        self.name = None  # type: str
        self.xml = xml  # type: ET.Element

    def read_from_xml(self, ctx: ImporterContext) -> None:
        xml = self.xml

        self.name = str(xml.text)
        self.protection = xml.get("prot")
        self.virtual = xml.get("virt")
        self.entity = ctx.getref(xml)

    def __repr__(self):
        return "<" + str(self.entity) + "|" + self.name + ">"


class ClassEntity(Entity):
    def __init__(self) -> None:
        super().__init__()

        # TODO: Use Protection class
        self.protection = None  # type: str
        self.inherits_from = []  # type: List[Entity]
        self.derived = []  # type: List[Entity]
        self.members = []  # type: List[Entity]
        self.all_members = []  # type: List[Entity]
        self.inner_classes = []  # type: List[ClassEntity]

        # Namespace or class parent
        # If class, this is an inner class
        self.parent = None  # type: Entity

    # Parent in canonical path
    # if this is
    # A::B::C
    # Then the class C has the namespace B as parent
    # and Bs parent is A.
    # A has None as the parent.
    def parent_in_canonical_path(self) -> Entity:
        return self.parent

    def read_from_xml(self, ctx: ImporterContext) -> None:
        super().read_from_xml(ctx)
        xml = self.xml

        self.protection = xml.get("prot")
        self.members = gather_members(xml, ctx)

        self.briefdescription = xml.find("briefdescription")
        self.detaileddescription = xml.find("detaileddescription")

        self.final = xml.get("final") == "yes"
        self.sealed = xml.get("sealed") == "yes"
        self.abstract = xml.get("abstract") == "yes"

        self.inherits_from = [Extends(node) for node in xml.findall("basecompoundref")]
        for x in self.inherits_from:
            x.read_from_xml(ctx)

        self.derived = [ctx.getref(node) for node in xml.findall("derivedcompoundref")]

        self.inner_classes = [ctx.getref(node) for node in xml.findall("innerclass")]
        for inner_class in self.inner_classes:
            inner_class.parent = self

        # All members, also inherited ones
        self.all_members = [ctx.getref(m) for m in xml.find("listofallmembers")]
        for m in xml.find("listofallmembers"):
            if ctx.getref(m) is None:
                print("NULL REFERENCE " + str(m.find("name").text) + " " + str(m.find("scope").text))
                print("Sure not old files are in the xml directory")
