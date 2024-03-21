from dataclasses import dataclass
from .entity import Entity
from importer.importer_context import ImporterContext
from typing import List

@dataclass
class InnerPage:
   page: "PageEntity"
   fake: bool


class PageEntity(Entity):
    def __init__(self) -> None:
        super().__init__()

        self.innerpages: List[InnerPage] = []

        # The page which has this page as an inner page
        self.parent: "PageEntity" = None  # type: PageEntity
        self.include_in_filepath: bool = False
    
    def child_entities(self):
        return [p.page for p in self.innerpages if not p.fake]
    
    def visible_child_entities(self):
        return [p.page for p in self.innerpages]

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
        assert xml is not None

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

        # Note that the Doxygen subpage command has been redefined to emit an innerpage xml element
        self.innerpages = []
        order = 0
        for node in xml.iter():
            # innerpage_nodes = [node for node in xml.iter("innerpage")]
            if node.tag in ["innerpage", "fakeinnerpage"]:
                page = ctx.getref(node)
                if page is None:
                    print("Could not find inner page of " + self.short_name + " with id " + str(node.get("refid")))
                else:
                    assert(isinstance(page, PageEntity))
                    fake = node.tag == "fakeinnerpage"
                    self.innerpages.append(InnerPage(page, fake))
                    if not fake:
                        page.parent = self

