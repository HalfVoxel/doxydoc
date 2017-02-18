from .entity import Entity, gather_members
from .class_entity import ClassEntity
from importer.importer_context import ImporterContext


class NamespaceEntity(Entity):
    def __init__(self) -> None:
        super().__init__()

        self.innerclasses = []  # type: List[ClassEntity]
        self.innernamespaces = []  # type: List[NamespaceEntity]

        self.parent_namespace = None  # type: NamespaceEntity

    def parent_in_canonical_path(self) -> Entity:
        return self.parent_namespace

    def read_from_xml(self, ctx: ImporterContext) -> None:
        super().read_from_xml(ctx)
        xml = self.xml

        self.innerclasses = [ctx.getref(node) for node in xml.findall("innerclass")]
        self.innernamespaces = [ctx.getref(node) for node in xml.findall("innernamespace")]

        for innerclass in self.innerclasses:
            innerclass.parent = self

        for innernamespace in self.innernamespaces:
            innernamespace.parent_namespace = self

        self.members = gather_members(xml, ctx)
