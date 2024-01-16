from .entity import Entity
import xml.etree.ElementTree as ET
from importer.importer_context import ImporterContext
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from importer.entities.member_entity import MemberEntity

class EnumValueEntity(Entity):
    def __init__(self, enum: "MemberEntity") -> None:
        super().__init__()
        self.parent: "MemberEntity" = enum
        self.initializer: ET.Element = None
    
    def parent_in_canonical_path(self) -> Entity:
        return self.parent

    def read_from_xml(self, ctx: ImporterContext) -> None:
        super().read_from_xml(ctx)
        self.initializer = self.xml.find("initializer")
