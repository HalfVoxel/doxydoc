from .entity import Entity
from importer.importer_context import ImporterContext


class PageEntity(Entity):
    def __init__(self) -> None:
        super().__init__()

        self.subpages = []  # type: List[Entity]

        # TODO: Why subpages AND innerpages?
        self.innerpages = []  # type: List[Entity]

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

        title = xml.find("title")
        if title is not None and title.text is not None:
            self.name = Entity.formatname(str(title.text))
        else:
            self.name = ""

        self.subpages = [ctx.getref(node) for node in xml.findall("innerpage")]
        self.innerpages = self.subpages
