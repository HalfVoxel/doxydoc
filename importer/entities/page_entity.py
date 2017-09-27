from .entity import Entity
from importer.importer_context import ImporterContext
from typing import List


class PageEntity(Entity):
    def __init__(self) -> None:
        super().__init__()

        self.innerpages = []  # type: List[PageEntity]

        # The page which has this page as an inner page
        self.parent = None  # type: PageEntity

    def parent_in_canonical_path(self) -> Entity:
        return self.parent

    def default_name(self):
        if self.id == "indexpage":
            # The index page has an empty <title> tag
            return "Home"
        else:
            return "#" + self.kind + "#"

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

        order = xml.find(".//order")
        if order is not None:
            self.sorting_order = int(order.get("value"))

        self.innerpages = [ctx.getref(node) for node in xml.findall("innerpage")]
        for page in self.innerpages:
            assert(isinstance(page, PageEntity))
            page.parent = self

