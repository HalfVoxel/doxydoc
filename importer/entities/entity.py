import xml.etree.ElementTree as ET
import importer.importer_context
from typing import List


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
        self.deprecated = False
        self.sorting_order = 0
        self.kind = "<not set>"

    def __str__(self):
        return "Entity: " + self.id

    def parent_in_canonical_path(self) -> 'Entity':
        return None

    @staticmethod
    def formatname(name: str) -> str:
        return name.split("::")[-1]

    def default_name(self):
        return "#" + self.kind + "#"

    def read_base_xml(self) -> None:
        self.id = self.xml.get("id")
        self.kind = self.xml.get("kind")

    def read_from_xml(self, ctx: importer.importer_context.ImporterContext) -> None:
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
            self.name = self.default_name()

        if short_name_node is not None:
            self.short_name = Entity.formatname(str(short_name_node.text))
        else:
            self.short_name = self.default_name()

        self.briefdescription = xml.find("briefdescription")
        self.detaileddescription = xml.find("detaileddescription")

        # Find sections
        # TODO: Simplify and optimize
        section_xml = []  # type: List[ET.Element]
        xrefsects = []  # type: List[ET.Element]
        if self.briefdescription is not None:
            section_xml = (section_xml +
                           self.briefdescription.findall(".//sect1") +
                           self.briefdescription.findall(".//sect2") +
                           self.briefdescription.findall(".//sect3") +
                           self.briefdescription.findall(".//sect4"))

            xrefsects += self.briefdescription.findall(".//xrefsect")

        if self.detaileddescription is not None:
            section_xml = (section_xml +
                           self.detaileddescription.findall(".//sect1") +
                           self.detaileddescription.findall(".//sect2") +
                           self.detaileddescription.findall(".//sect3") +
                           self.detaileddescription.findall(".//sect4"))

            xrefsects += self.detaileddescription.findall(".//xrefsect")

        self.sections = [ctx.getentity(sec) for sec in section_xml if ctx.getentity(sec) is not None]

        for xref in xrefsects:
            id = xref.get("id")

            # This is based on how Doxygen generates the id, which looks (for example) like
            # deprecated_1_deprecated000018
            # This will extract 'deprecated' as the key
            assert("_" in id)
            key = id.split("_")[0]
            if key == "deprecated":
                # Detected that the entity is deprecated
                # This is not a completely accurate check as there might be some other thing in the description that was marked as deprecated
                self.deprecated = True


def gather_members(xml, ctx: importer.importer_context.ImporterContext) -> List[Entity]:
    return [ctx.getentity(memberdef) for memberdef in xml.findall("sectiondef/memberdef")]
