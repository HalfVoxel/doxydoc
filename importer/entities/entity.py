import xml.etree.ElementTree as ET
import importer.importer_context
from importer.location import Location
from typing import List, Union, Optional, cast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from importer import Importer


def try_strip(x: Optional[str]):
    '''Tries to strip spacing and dots from strings'''
    return x.strip(" .\t\n") if x is not None else None


def elements_equal(e1: ET.Element, e2: ET.Element):
    if e1.tag != e2.tag:
        return False
    if try_strip(e1.text) != try_strip(e2.text):
        return False
    if try_strip(e1.tail) != try_strip(e2.tail):
        return False
    if e1.attrib != e2.attrib:
        return False
    if len(e1) != len(e2):
        return False
    return all(elements_equal(c1, c2) for c1, c2 in zip(e1, e2))


class Entity:
    def __init__(self) -> None:
        self.name = ""  # type: str
        self.short_name = ""  # type: str
        self.name_with_generics = ""  # type: str
        self.briefdescription = None  # type: Optional[ET.Element]
        self.detaileddescription = None  # type: Optional[ET.Element]
        self.id = ""  # type: str
        self.xml = None  # type: Optional[ET.Element]
        # Sections in descriptions that can be linked to
        self.sections = []  # type: List[Entity]
        self.deprecated = False
        self.sorting_order = 0
        self.kind = "<not set>"
        # The filename of the xml file that produced this entity
        self.filename = None  # type: Union[None,str]
        self.location = None  # type: Location

        # If false then this entity will not show up in any file paths (except for the entity itself)
        # For example if the page tutorials/get_started exists then normally that page would be placed at
        # tutorials/get_started.html, however if the tutorials entity has this option disabled then it will
        # be placed at get_started.html.
        self.include_in_filepath = False

    def child_entities(self):
        return self.sections
    
    def visible_child_entities(self):
        return []

    def __str__(self) -> str:
        return f"<{self.name} kind={self.kind} id={self.id}>"

    def parent_in_canonical_path(self) -> 'Optional[Entity]':
        return None

    def full_canonical_path(self, separator="."):
        return separator.join([e.name for e in self.full_canonical_path_list()])

    def full_canonical_path_list(self) -> List['Entity']:
        e = self
        ss = []
        while e is not None:
            ss.append(e)
            e = e.parent_in_canonical_path()

        ss.reverse()
        return ss

    @staticmethod
    def formatname(name: str) -> str:
        return name.split("::")[-1]

    def default_name(self):
        return "#" + self.kind + "#"

    def read_base_xml(self) -> None:
        assert(self.xml is not None)
        self.id = self.xml.get("id")
        self.kind = self.xml.get("kind")
        loc = self.xml.find("location")
        if loc is not None:
            self.location = Location()
            self.location.read_from_xml(loc)

    def read_from_xml(self, ctx: importer.importer_context.ImporterContext) -> None:
        xml = self.xml
        assert(xml is not None)

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
        
        self.name_with_generics = self.name

        self.briefdescription = xml.find("briefdescription")
        if self.briefdescription is not None and all(len(t.strip()) == 0 for t in self.briefdescription.itertext()) and all(x.tag in ["para", "order", "briefdescription"] for x in self.briefdescription.iter()):
            # Empty brief
            # Doxygen seems to generate empty brief descriptions as "<p>   </p>" sometimes, which we don't want.
            self.briefdescription.clear()

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
            # Even though doxygen's REPEAT_BRIEF option is set to NO, it will still repeat the brief for pages.
            if self.briefdescription is not None:
                brief_para: Optional[ET.Element] = next(iter(self.briefdescription), None)
                detailed_para: Optional[ET.Element] = next(iter(self.detaileddescription), None)
                if brief_para is not None and detailed_para is not None and brief_para.tag == "para":
                    if elements_equal(brief_para, detailed_para):
                        self.detaileddescription.remove(detailed_para)
                    elif detailed_para.text is not None and brief_para.text is not None and detailed_para.text.strip().startswith(brief_para.text.strip()):
                        detailed_para.text = detailed_para.text.strip()[len(brief_para.text.strip()):].strip()

            section_xml = (section_xml +
                           self.detaileddescription.findall(".//sect1") +
                           self.detaileddescription.findall(".//sect2") +
                           self.detaileddescription.findall(".//sect3") +
                           self.detaileddescription.findall(".//sect4"))

            xrefsects += self.detaileddescription.findall(".//xrefsect")

        self.sections = [e for e in map(ctx.getentity, section_xml) if e is not None]

        for xref in xrefsects:
            id = xref.get("id")

            # This is based on how Doxygen generates the id, which looks (for example) like
            # deprecated_1_deprecated000018
            # This will extract 'deprecated' as the key
            assert("_" in id)
            key = id.split("_")[0]
            if key == "deprecated":
                # TODO
                # Detected that the entity is deprecated
                # This is not a completely accurate check as there might be some other thing in the description that was marked as deprecated
                self.deprecated = True

    def post_xml_read(self, state: 'Importer') -> None:
        ''' Called when all entities' read_from_xml methods have been called '''

        # Resolve copydocs
        # We need to do this iteratively since we may copy the docs from some object that also tries to copy the docs from something else
        while True:
            copydoc = self.briefdescription.find(".//copydoc") if self.briefdescription is not None else None
            if copydoc is None and self.detaileddescription is not None:
                copydoc = self.detaileddescription.find(".//copydoc")
            if copydoc is None:
                break
            
            if len(copydoc) != 0:
                raise Exception("Invalid copydoc command. Expected no children")
            if copydoc.text is None:
                raise Exception("Invalid copydoc command. Expected a target name")

            entity = state.getref_from_name(copydoc.text, self.parent_in_canonical_path(), ignore_overloads=True)
            if entity is None:
                raise Exception(f"Invalid copydoc command. Could not resolve target: '{copydoc.text}' in the scope of {self.parent_in_canonical_path().full_canonical_path()}")
            
            remove_and_simplify(self.briefdescription, copydoc)
            remove_and_simplify(self.detaileddescription, copydoc)
            
            self.briefdescription = combine_tags("briefdescription", list(entity.briefdescription) + list(self.briefdescription))
            self.detaileddescription = combine_tags("detaileddescription", list(entity.detaileddescription) + list(self.detaileddescription))


def remove_and_simplify(parent: ET.Element, needle: ET.Element):
    for child in parent:
        if child == needle:
            parent.remove(child)
        else:
            if not remove_and_simplify(child, needle):
                parent.remove(child)
    
    if parent.tag in ["para"] and len(parent) == 0 and (parent.text + parent.tail).strip() in ["", "."]:
        parent.clear()
        return False
    
    return True

def combine_tags(tag: str, tags: List[ET.Element]) -> ET.Element:
    wrapper = ET.Element(tag)
    for tag in tags:
        wrapper.append(tag)
    return wrapper

def gather_members(xml, ctx: importer.importer_context.ImporterContext) -> List[Entity]:
    result = [ctx.getentity(memberdef) for memberdef in xml.findall("sectiondef/memberdef")]
    assert None not in result
    return cast(List[Entity], result)
