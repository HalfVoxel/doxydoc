from .entity import Entity, gather_members
from typing import Dict
import xml.etree.ElementTree as ET
from importer.importer_context import ImporterContext


class FileEntity(Entity):
    def __init__(self) -> None:
        super().__init__()

        self.innerclasses = []  # type: List[Entity]
        self.innernamespaces = []  # type: List[Entity]
        self.contents = None  # type: ET.Element
        self.location = None  # type: str # TODO: Unknown location
        # TODO gather_members

    def read_from_xml(self, ctx: ImporterContext) -> None:
        super().read_from_xml(ctx)
        xml = self.xml

        self.innerclasses = [ctx.getref(node) for node in xml.findall("innerclass")]
        self.innernamespaces = [ctx.getref(node) for node in xml.findall("innernamespace")]

        self.contents = xml.find("programlisting")

        self.members = gather_members(xml, ctx)
        # Only one members list
        self.all_members = self.members

        # Find location of file
        loc = xml.find("location")
        self.location = loc.get("file") if loc is not None else None
