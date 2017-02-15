from .entity import Entity
from typing import Dict
import xml.etree.ElementTree as ET
from importer.importer_context import ImporterContext


class ExternalEntity(Entity):
    def read_from_xml(self, ctx: ImporterContext) -> None:
        # Nothing to read since this
        # entity is not based on an XML file
        pass
