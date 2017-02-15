from pprint import pprint
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
import importer.entities as entities
from importer.entities import Entity
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
        self._xml2entity = {}  # type: Dict[ET.Element,Entity]

    def iter_unique_docobjs(self):
        for k, v in self._docobjs.items():
            if k == v.id:
                yield v

    def _add_docobj(self, obj: Entity, id: str=None):
        if id is None:
            id = obj.id
        self._docobjs[id] = obj
        # Workaround for doxygen apparently generating refid:s which do not exist as id:s
        id2 = obj.id + "_1" + obj.id
        self._docobjs[id2] = obj
        self.entities.append(obj)

    def get_entity(self, id):
        return self._docobjs[id]

    def _create_entity(self, xml, parent_entity=None):
        kind = xml.get("kind")

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
        xml.set("docobj", entity)
        self._xml2entity[xml] = entity
        return entity

    def read(self, xml_filenames):
        roots = []

        for fname in xml_filenames:
            dom = ET.parse(fname)
            assert dom is not None, "No DOM"

            root = dom.getroot()
            assert root is not None, "No Root"

            compound = root.find("compounddef")

            if compound is not None:
                self._register_compound(compound)
                roots.append(root)

        self._process_references(roots)
        self._read_entity_xml()

    def _read_entity_xml(self):
        for entity in self.entities:
            try:
                entity.read_from_xml(self._xml2entity)
            except:
                print("Exception when parsing " + str(entity.id) + " of type " + str(entity.kind))
                raise

    def _process_references(self, roots):
        for root in roots:
            self._process_references_root(root)

    def _process_references_root(self, xml):
        for node in xml.iter():
            id = node.get("refid")
            if id is not None:
                try:
                    # Doxygen can sometimes generate refid=""
                    obj = self.get_entity(id)
                    node.set("ref", obj)
                except KeyError:
                    # raise
                    pass

    def _register_compound(self, xml):

        entity = self._create_entity(xml)

        # Will only be used for debugging if even that. Formatted name will be added later
        entity.name = xml.find("compoundname").text

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


def is_detail_hidden(member, settings):
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


class DocMember:
    pass


class NavItem:
    def __init__(self):
        self.label = ""
        self.obj = None
        self.url = None


def dump(obj):
    pprint(vars(obj))
