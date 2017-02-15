from .entity import Entity
from typing import Dict
import xml.etree.ElementTree as ET


class PageEntity(Entity):
    def __init__(self):
        super().__init__()

        self.subpages = []

        # TODO: Why subpages AND innerpages?
        self.innerpages = []

    def read_from_xml(self, xml2entity: Dict[ET.Element, Entity]) -> None:
        super().read_from_xml(xml2entity)
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

        self.subpages = [node.get("ref") for node in xml.findall("innerpage")]
        for p in self.subpages:
            p.parentpage = self

        self.innerpages = self.subpages
