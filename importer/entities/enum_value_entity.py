from .entity import Entity
import xml.etree.ElementTree as ET
from importer.importer_context import ImporterContext


class EnumValueEntity(Entity):
    def __init__(self) -> None:
        super().__init__()
        self.initializer = None  # type: ET.Element

    def read_from_xml(self, ctx: ImporterContext) -> None:
        super().read_from_xml(ctx)
        self.initializer = self.xml.find("initializer")
