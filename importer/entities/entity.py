import xml.etree.ElementTree as ET
from typing import Dict


def gather_members(xml):
    return [memberdef.get("docobj") for memberdef in xml.findall("sectiondef/memberdef")]


class Entity:
    def __init__(self) -> None:
        self.name = ""  # type: str
        self.short_name = ""  # type: str
        self.briefdescription = None  # type: ET.Element
        self.detaileddescription = None  # type: ET.Element
        self.id = ""  # type: str
        self.xml = None  # type: ET.Element
        # Sections in descriptions that can be linked to
        self.sections = []  # type: List[Entity]

    def __str__(self):
        return "Entity: " + self.id

    @staticmethod
    def formatname(name: str) -> str:
        return name.split("::")[-1]

    def read_base_xml(self) -> None:
        self.id = self.xml.get("id")
        self.kind = self.xml.get("kind")

    def read_from_xml(self, xml2entity: Dict[ET.Element, 'Entity']) -> None:
        xml = self.xml

        short_name_node = xml.find("compoundname")
        name_node = xml.find("title")

        if name_node is None:
            name_node = xml.find("name")
        if name_node is None:
            name_node = short_name_node

        if short_name_node is None:
            short_name_node = name_node

        if name_node is not None and name_node.text is not None:
            self.name = Entity.formatname(str(name_node.text))
        else:
            self.name = "#" + self.kind + "#"

        if short_name_node is not None:
            self.short_name = Entity.formatname(str(short_name_node.text))
        else:
            self.short_name = "#" + self.kind + "#"

        self.briefdescription = xml.find("briefdescription")
        self.detaileddescription = xml.find("detaileddescription")

        # Find sections
        # TODO: Simplify and optimize
        section_xml = []  # type: List[ET.Element]
        if self.briefdescription is not None:
            section_xml = (section_xml +
                           self.briefdescription.findall(".//sect1") +
                           self.briefdescription.findall(".//sect2") +
                           self.briefdescription.findall(".//sect3") +
                           self.briefdescription.findall(".//sect4"))

        if self.detaileddescription is not None:
            section_xml = (section_xml +
                           self.detaileddescription.findall(".//sect1") +
                           self.detaileddescription.findall(".//sect2") +
                           self.detaileddescription.findall(".//sect3") +
                           self.detaileddescription.findall(".//sect4"))

        self.sections = [xml2entity[sec] for sec in section_xml if sec.get("docobj") is not None]
