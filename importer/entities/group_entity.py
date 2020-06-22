from .entity import Entity
from importer.importer_context import ImporterContext
from typing import List


class GroupEntity(Entity):
    def __init__(self) -> None:
        super().__init__()
        self.inner_classes = []  # type: List[Entity]
        self.inner_namespaces = []  # type: List[Entity]
        self.inner_groups = []  # type: List[Entity]
        self.parent = None  # type: Entity
    
    def child_entities(self):
        return self.inner_classes + self.inner_namespaces + self.inner_groups

    def parent_in_canonical_path(self) -> Entity:
        return self.parent

    def read_from_xml(self, ctx: ImporterContext) -> None:
        super().read_from_xml(ctx)
        xml = self.xml
        assert xml is not None

        self.title = Entity.formatname(str(xml.find("title").text))

        self.inner_classes = [ctx.getref(node) for node in xml.findall("innerclass")]
        self.inner_namespaces = [ctx.getref(node) for node in xml.findall("innernamespace")]

        self.inner_groups = [ctx.getref(node) for node in xml.findall("innergroup")]
