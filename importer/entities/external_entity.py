from .entity import Entity
from importer.importer_context import ImporterContext


class ExternalEntity(Entity):
    def __init__(self, url: str) -> None:
        super().__init__()
        self.exturl = url

    def read_from_xml(self, ctx: ImporterContext) -> None:
        # Nothing to read since this
        # entity is not based on an XML file
        pass
