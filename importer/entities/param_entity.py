from .entity import Entity
from typing import Optional
import xml.etree.ElementTree as ET
from importer.importer_context import ImporterContext
from html import unescape


class ParamEntity(Entity):
    def __init__(self) -> None:
        super().__init__()

        self.type: Optional[ET.Element] = None
        self.default_value: Optional[ET.Element] = None
        self.typename: Optional[str] = None

    def read_from_xml(self, ctx: ImporterContext) -> None:
        xml = self.xml
        assert xml is not None

        self.name_with_generics = self.name = str(xml.find("declname").text)
        self.type = xml.find("type")
        self.default_value = xml.find("defval")

        def normalize(text: str):
            text = unescape(text)
            if text.startswith("ref "):
                text = text[len("ref "):]
            if text.startswith("out "):
                text = text[len("out "):]
            return text

        typename = ""
        for elem in self.type.iter():
            if elem.text is not None:
                typename += normalize(elem.text)
            if elem.tail is not None:
                typename += normalize(elem.tail)

        typename = typename.replace(" ", "").replace("\n", "").replace("\t", "")
        self.typename = typename
