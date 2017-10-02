from .entity import Entity
import xml.etree.ElementTree as ET
from importer.importer_context import ImporterContext


class SectEntity(Entity):
    def __init__(self) -> None:
        super().__init__()
        self.title = None  # type: ET.Element

    def read_from_xml(self, ctx: ImporterContext) -> None:
        self.title = self.xml.find("title")
        # Doxygen generates the ID as "pagename_1realname"
        # so we try to extract it here
        self.name = self.id.split("_1")[-1]
