from .entity import Entity
from importer.importer_context import ImporterContext


class GroupEntity(Entity):
    def __init__(self) -> None:
        super().__init__()
        self.innerclasses = []  # type: List[Entity]
        self.innernamespaces = []  # type: List[Entity]
        self.innergroups = []  # type: List[Entity]

    def read_from_xml(self, ctx: ImporterContext) -> None:
        super().read_from_xml(ctx)
        xml = self.xml

        self.title = Entity.formatname(str(xml.find("title").text))

        self.innerclasses = [ctx.getref(node) for node in xml.findall("innerclass")]
        self.innernamespaces = [ctx.getref(node) for node in xml.findall("innernamespace")]

        self.innergroups = [ctx.getref(node) for node in xml.findall("innergroup")]
