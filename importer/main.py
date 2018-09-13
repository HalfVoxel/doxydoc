from pprint import pprint
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
from importer.importer_context import ImporterContext
import importer.entities as entities
from importer.entities import Entity
from typing import Iterable, List, Dict
FILE_EXT = ".html"
OUTPUT_DIR = "html"

# escape() and unescape() takes care of &, < and >.
html_escape_table = {
    '"': "&quot;",
    "'": "&apos;"
}
html_unescape_table = {v: k for k, v in html_escape_table.items()}


def paramescape(v):
    return escape(v, html_escape_table)


class Importer:

    def __init__(self) -> None:
        self.entities = []  # type: List[Entity]
        self._docobjs = {}  # type: Dict[str,Entity]
        self.ctx = ImporterContext()

    def iter_unique_docobjs(self) -> Iterable[Entity]:
        for k, v in self._docobjs.items():
            if k == v.id:
                yield v

    def _add_docobj(self, obj: Entity, id: str=None) -> None:
        if id is None:
            id = obj.id
        self._docobjs[id] = obj
        # Workaround for doxygen apparently generating refid:s which do not exist as id:s
        # e.g links to pages show up as 'modifiers_1modifiers' or 'graph_types_1graphTypes'
        id2 = obj.id + "_1" + obj.id
        id3 = obj.id + "_1" + obj.short_name
        self._docobjs[id2] = obj
        self._docobjs[id3] = obj
        self.entities.append(obj)

    def get_entity(self, id: str) -> Entity:
        return self._docobjs[id]

    def get_entity_by_path(self, name: str) -> Entity:
        '''
        Returns an entity using for example a classname like Pathfinding.Util.ListPool.
        If the name is ambigious, for example if there is one class named Namespace1.Blah and another one name Namespace2.Blah and the specified name is Blah, then an exception will be thrown.
        '''
        parts = name.strip().replace("::", ".").split(".")
        candidates = []
        for entity in self.entities:
            index = len(parts)-1
            e = entity
            assert type(e) is not str, e
            while e is not None and index >= 0 and e.name == parts[index]:
                index -= 1
                e = e.parent_in_canonical_path()
                assert type(e) is not str, e

            if index < 0:
                # Matched completely
                candidates.append(entity)

        if len(candidates) > 1:
            raise Exception(f"Ambigious reference '{name}', there are {len(candidates)} candiates that matches\n" + ", ".join(e.name for e in candidates))

        return candidates[0]

    def _create_entity(self, xml: ET.Element, parent_entity: Entity=None) -> Entity:
        kind = xml.get("kind")
        entity = None  # type: Entity

        if kind == "class" or kind == "struct" or kind == "interface":
            entity = entities.ClassEntity()
        elif kind == "file":
            entity = entities.FileEntity()
        elif kind == "namespace":
            entity = entities.NamespaceEntity()
        elif kind == "group":
            entity = entities.GroupEntity()
        elif kind == "page":
            entity = entities.PageEntity()
        elif kind == "example":
            entity = entities.ExampleEntity()
        elif (kind == "define" or
                kind == "property" or
                kind == "event" or
                kind == "variable" or
                kind == "typedef" or
                kind == "enum" or
                kind == "function" or
                kind == "signal" or
                kind == "prototype" or
                kind == "friend" or
                kind == "dcop" or
                kind == "slot"):
            entity = entities.MemberEntity()
            assert(parent_entity is not None)
            entity.defined_in_entity = parent_entity
        elif (kind == "union" or
                kind == "protocol" or
                kind == "category" or
                kind == "exception" or
                kind == "dir"):
            # Unsupported known entity type
            entity = entities.Entity()
        elif kind is None and "sect" in xml.tag:
            # Valid for things like sect[1-4]
            entity = entities.SectEntity()
        else:
            print("Unexpected kind: " + kind)
            entity = entities.Entity()

        entity.xml = xml
        entity.read_base_xml()

        if entity.id == "":
            print("Warning: Found an entity without an ID. Skipping")
            return None

        self._add_docobj(entity)
        self.ctx.setentity(xml, entity)
        return entity

    def read(self, xml_filenames: List[str]) -> None:
        roots = []

        for fname in xml_filenames:
            try:
                dom = ET.parse(fname)
                assert dom is not None, "No DOM"

                root = dom.getroot()
                assert root is not None, "No Root"

                compound = root.find("compounddef")

                if compound is not None:
                    self._register_compound(compound, fname)
                    roots.append(root)
            except Exception as e:
                raise Exception("Could not parse '" + fname + "'") from e

        for root in roots:
            merge_simple_sections(root)
        self._process_references(roots)
        self._read_entity_xml()

    def _read_entity_xml(self) -> None:
        for entity in self.entities:
            try:
                entity.read_from_xml(self.ctx)
            except:
                print("Exception when parsing " + str(entity.id) + " of type " + str(entity.kind))
                raise

        for entity in self.entities:
            try:
                entity.post_xml_read()
            except:
                print("Exception when post processing " + str(entity.id) + " of type " + str(entity.kind))
                raise

    def _process_references(self, roots: List[ET.Element]) -> None:
        for root in roots:
            self._process_references_root(root)

    def _process_references_root(self, xml: ET.Element) -> None:
        for node in xml.iter():
            id = node.get("refid")
            if id is not None:
                try:
                    # Doxygen can sometimes generate refid=""
                    obj = self.get_entity(id)
                    self.ctx.setref(node, obj)
                except KeyError:
                    # raise
                    pass

    def _register_compound(self, xml: ET.Element, filename: str) -> None:

        entity = self._create_entity(xml)

        entity.filename = filename

        # Will only be used for debugging if even that. Formatted name will be added later
        entity.name = str(xml.find("compoundname").text)

        memberdefs = xml.findall("sectiondef/memberdef")
        for member in memberdefs:
            self._create_entity(member, entity)

        # Find sect[1-4]
        sects = (xml.findall(".//sect1") +
                 xml.findall(".//sect2") +
                 xml.findall(".//sect3") +
                 xml.findall(".//sect4"))

        for sect in sects:
            entity = self._create_entity(sect, entity)

        # Can be added later
        # For plugins to be able to extract more entities from the xml
        # ids = xml.findall(".//*[@id]")

        # parent = entity

        # for idnode in ids:

        #     entity, ok = try_call_function("parseid_" + idnode.tag, idnode)
        #     if not ok:
        #         entity = Entity()
        #         entity.id = idnode.get("id")
        #         entity.kind = idnode.get("kind")

        #         # print(idnode.get("id"))
        #         namenode = idnode.find("name")

        #         if namenode is not None:
        #             entity.name = namenode.text
        #         else:
        #             entity.name = "<undefined " + idnode.tag + "-" + entity.id + " >"

        #         entity.anchor = entity.name

        #     if entity is not None:
        #         entity.compound = parent

        #         idnode.set("docobj", entity)
        #         self._add_docobj(entity)
        #         # print(entity.full_url())


def merge_simple_sections(xml: ET.Element):
    ''' Combines consecutive simplesect tags into a single simplesect tag. This is used for e.g the \see command '''
    items = []
    for node in xml.iter():
        spans = []  # type: List[List[ET.Element]]
        current_span = []  # type: List[ET.Element]
        kind = ""
        for child in node:
            if child.tag == "simplesect":
                # Split span because of change in kind
                if child.get("kind") != kind:
                    if len(current_span) > 0:
                        spans.append(current_span)
                    current_span = []

                kind = child.get("kind")
                current_span.append(child)

                # Split span because of trailing text
                if child.tail.strip() != "":
                    spans.append(current_span)
                    current_span = []
                    kind = ""
            else:
                # Split span because of a different tag
                if len(current_span) > 0:
                    spans.append(current_span)
                    current_span = []
                    kind = ""

        if len(current_span) > 0:
            spans.append(current_span)

        items.append((node, spans))

    for node, spans in items:
        for span in spans:
            # Remove all but the last child
            for child in span[:-1]:
                node.remove(child)

            # Insert the content from the other simplesect nodes into the last one
            for child in reversed(span[:-1]):
                for subchild in reversed(list(child)):
                    span[-1].insert(0, subchild)


def is_detail_hidden(member, settings) -> bool:
    """Returns if the member's detailed view should be hidden"""

    # Enums show up as members, but they should always be shown.
    if member.kind == "enum":
        return False

    # Check if the member is undocumented
    if settings.hide_undocumented and (
        member.detaileddescription.text is None or member.detaileddescription.text.isspace()
    ):
        if member.detaileddescription.text is None:
            return True

        count = 0
        for v in member.detaileddescription.iter():
            count += 1
            if (count > 1):
                break

        # If we only visited the root node (member.detaileddescription)
        # then it has no children and so the detaileddescription is empty
        if count == 1:
            return True

    return False


class NavItem:
    def __init__(self) -> None:
        self.label = ""
        self.obj = None  # type: Entity
        self.url = None  # type: str


def dump(obj) -> None:
    pprint(vars(obj))
