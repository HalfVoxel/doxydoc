from .entity import Entity, gather_members
from .class_entity import ClassEntity
from importer.importer_context import ImporterContext


class NamespaceEntity(Entity):
    def __init__(self) -> None:
        super().__init__()

        self.inner_classes = []  # type: List[ClassEntity]
        self.inner_namespaces = []  # type: List[NamespaceEntity]

        self.parent_namespace = None  # type: NamespaceEntity

    def parent_in_canonical_path(self) -> Entity:
        return self.parent_namespace

    def read_from_xml(self, ctx: ImporterContext) -> None:
        super().read_from_xml(ctx)
        xml = self.xml

        self.inner_classes = [ctx.getref(node) for node in xml.findall("innerclass")]
        self.inner_namespaces = [ctx.getref(node) for node in xml.findall("innernamespace")]

        for innerclass in self.inner_classes:
            innerclass.parent = self

        for innernamespace in self.inner_namespaces:
            innernamespace.parent_namespace = self

        self.members = gather_members(xml, ctx)
