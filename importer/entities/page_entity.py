from .entity import Entity
from importer.importer_context import ImporterContext


class PageEntity(Entity):
    def __init__(self) -> None:
        super().__init__()

        self.innerpages = []  # type: List[PageEntity]

        # The page which has this page as an inner page
        self.parent = None  # type: PageEntity

    def parent_in_canonical_path(self) -> Entity:
        return self.parent

    def read_from_xml(self, ctx: ImporterContext) -> None:
        super().read_from_xml(ctx)
        xml = self.xml

        # xml
        # id
        # name
        # kind
        # briefdesc
        # detaileddesc
        # innerpage

        self.innerpages = [ctx.getref(node) for node in xml.findall("innerpage")]
        for page in self.innerpages:
            assert(isinstance(page, PageEntity))
            page.parent = self
