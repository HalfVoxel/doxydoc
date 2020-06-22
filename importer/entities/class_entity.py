from .entity import Entity, gather_members
from importer.protection import Protection
from typing import Dict, List
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
        self.inherits_from = []  # type: List[Extends]
        self.derived = []  # type: List[Entity]
        self.members = []  # type: List[Entity]
        self.all_members = []  # type: List[Entity]
        self.inner_classes = []  # type: List[ClassEntity]

        # Namespace or class parent
        # If class, this is an inner class
        self.parent = None  # type: Entity
    
    def child_entities(self):
        return self.derived + self.all_members

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
        assert xml is not None

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

        for m in xml.find("listofallmembers"):
            if ctx.getref(m) is None:
                print("NULL REFERENCE " + str(m.find("name").text) + " " + str(m.find("scope").text))
                print("Sure not old files are in the xml directory")

    def post_xml_read(self) -> None:
        self.all_members = []
        gather_all_members(self, self, self.all_members)
        self.all_members.sort(key=lambda m: (m.name.lower(), len(m.params), m.id))


def gather_all_members(root_entity, entity, all_members):
    def valid_member(m):
        # The name check is done to prevent constructors showing up as inherited members
        if m.defined_in_entity != root_entity and m.defined_in_entity.name == m.name:
            # Is constructor in base class
            return False

        if m.protection == "private" and m.defined_in_entity != root_entity:
            # Private member in base class is not treated as a member of the subclass
            return False

        for m2 in m.reimplementedby:
            if m2 in all_members:
                return False

        if m.abstract and m.defined_in_entity != root_entity:
            # Abstract member in base class
            # Doxygen will not add a reimplementedby section for this member
            # so the check above will not work.
            # We still don't want this is subclasses though.
            # TODO: An abstract class that does not override this method might want to show it in the docs though.
            return False

        return True

    all_members += [m for m in entity.members if valid_member(m)]

    for parent in entity.inherits_from:
        parent_entity = parent.entity

        if parent_entity is None:
            # Unknown entity. Likely some library class that was not scanned by Doxygen
            continue

        if parent_entity.kind == "interface" and entity.kind != "interface":
            continue

        gather_all_members(root_entity, parent_entity, all_members)
