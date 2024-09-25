from importer.entities.class_entity import ClassEntity
from importer.entities.namespace_entity import NamespaceEntity
from importer.entities.overload_entity import OverloadEntity
from importer.entities.member_entity import MemberEntity
from pprint import pprint
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
from importer.importer_context import ImporterContext
import importer.entities as entities
from importer.entities import Entity
from typing import Iterable, List, Dict, Optional, Tuple
import re
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
        self.resolve_cache: Dict[Tuple[str, Optional[Entity], bool], Optional[Entity]] = {}
        self.name_to_entities: Dict[str, List[Entity]] = {}
        self.id_to_entity: Dict[str, Entity] = {}
        self.canonical_path_to_entities: Dict[str, List[Entity]] = {}
        self.cache_dirty = False

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
        self.cache_dirty = True

    def rebuild_caches(self):
        if not self.cache_dirty:
            return

        self.name_to_entities = {}
        self.id_to_entity = {}
        self.canonical_path_to_entities = {}
        for entity in self.entities:
            if entity.name not in self.name_to_entities:
                self.name_to_entities[entity.name] = []
            self.name_to_entities[entity.name].append(entity)

            if entity.id != "":
                if entity.id in self.id_to_entity:
                    print(f"Duplicate id {entity.id}")
                else:
                    assert entity.id not in self.id_to_entity, f"Duplicate id {entity.id}"
                    self.id_to_entity[entity.id] = entity

            canonical_path = entity.full_canonical_path_list()
            for i in range(len(canonical_path)):
                path = ".".join(e.name for e in canonical_path[i:])
                if path not in self.canonical_path_to_entities:
                    self.canonical_path_to_entities[path] = []
                self.canonical_path_to_entities[path].append(entity)

        self.cache_dirty = False


    def get_entity(self, id: str) -> Entity:
        return self._docobjs[id]

    def try_get_entity(self, id: str) -> Optional[Entity]:
        return self._docobjs.get(id)

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
            with open(fname, "r", encoding="utf-8") as f:
                text = f.read()
                def replace_reflink(match):
                    args = match.group(1).split(";")
                    # Convert this node to an anchor node
                    # We need to do this here, because our version of doxygen does not support multiple arguments to the ref command with a
                    # separator that is not a comma. So we do the splitting here instead.
                    # It's very ugly.
                    # And also. Doxygen cannot escape the generics for us. So when using generics, the output may become invalid xml.
                    # So we need to do this replacement before we even parse the xml file.
                    id = escape(args[0])
                    if len(args) > 2:
                        print(f"Warning: Could not parse reflink with more than 2 arguments: {match.group(1)}")
                    if len(args) > 1:
                        title = escape(args[1])
                        return f"<ulink url=\"ref:{id}\">{title}</ulink>"
                    else:
                        return f"<ulink url=\"ref:{id}\">{id}</ulink>"
                text = re.sub(r"<reflink\s+href=\"([^\"]*)\"\s*\/>", replace_reflink, text)

            try:
                root = ET.fromstring(text)
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
        sub_entities = []
        for entity in self.entities:
            try:
                entity.read_from_xml(self.ctx)
                if isinstance(entity, MemberEntity) and entity.kind == "enum":
                    sub_entities += entity.members
            except:
                print("Exception when parsing " + str(entity.id) + " of type " + str(entity.kind))
                raise

        self.entities += sub_entities

        for entity in self.entities:
            try:
                entity.post_xml_read(self)
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

    def getref_from_name(self, name: str, resolve_scope: Optional[Entity], ignore_overloads: bool=False) -> Entity:
        name = name.strip()
        name = name.replace("::", ".")

        # Resolve references in member entities as if we resolve from the associated class
        if resolve_scope is not None and type(resolve_scope) is MemberEntity:
            resolve_scope = resolve_scope.parent_in_canonical_path()

        key = (name, resolve_scope, ignore_overloads)
        if key in self.resolve_cache:
            return self.resolve_cache[key]

        debug = False # resolve_scope is not None and resolve_scope.full_canonical_path() == "Pathfinding.AIPath" and name == "destination"
        if debug:
            print("\n\n\n\n\n\nRESOLVING " + name + "\n\n\n\n\n")

        res = self.getref_from_name_inner(name, resolve_scope, ignore_overloads, debug)
        self.resolve_cache[key] = res
        if debug:
            print("Resolved to " + (res.full_canonical_path() if res is not None else "None"))

        return res

    def getref_from_name_inner(self, name: str, resolve_scope: Optional[Entity], ignore_overloads: bool, debug: bool) -> Entity:
        kind_filter = None
        parts = name.split("!")
        self.rebuild_caches()

        if len(parts) > 1:
            assert len(parts) == 2
            name = parts[0]
            kind_filter = parts[1]

        if "(" in name:
            pathPart, paramPart = name.split("(")
            pathPart = pathPart.strip()
            paramPart = paramPart.replace(" ", "").strip()

            if not paramPart.endswith(")"):
                print(f"Expected parameter list to end with a closing parenthesis: '{name}'. Parameters list: '{paramPart}'")
                return None
            # Remove ending paren
            paramPart = paramPart[:-1]
        else:
            pathPart = name
            paramPart = None

        candidates: List[Entity] = []

        # For most entities, their id is equal to their name,
        # but for some entities (e.g. pages) this is not the case.
        matching_id = self.id_to_entity.get(pathPart)
        if matching_id is not None:
            assert matching_id.id == pathPart
            candidates.append(matching_id)

        for entity in self.canonical_path_to_entities.get(pathPart, []):
            candidates.append(entity)

        def params_for_entity(entity: Entity):
            # Only member entities have parameters.
            # External entities may also be functions, but we do not know the parameters for those
            return entity.params if type(entity) is MemberEntity else []

        # Try resolving locally
        def resolveLocal(scope: Entity, path: List[str], params: Optional[str]):
            if debug:
                print("Resolving locally " + scope.full_canonical_path() + " -> " + str(path))

            if len(path) > 0:
                jump_candidates = []
                if type(scope) is MemberEntity:
                    # Jump to the member's type
                    jump_scope = scope.get_simple_type(self.ctx)
                    if jump_scope is not None:
                        if debug:
                            print("Jumping to member type " + jump_scope.name)
                        jump_candidates = resolveLocal(jump_scope, path, params)
                    else:
                        if debug:
                            print("No jump target for " + scope.name + " of type " + scope.kind + " " + ET.tostring(scope.type, encoding="unicode"))

                potential_children = [c for c in scope.child_entities() if c.name == path[0]]
                return jump_candidates + [candidate for child in potential_children for candidate in resolveLocal(child, path[1:], params)]
            else:
                if params is None:
                    return [scope]
                else:
                    candidateParamNames = ",".join(param.typename for param in params_for_entity(scope))
                    if candidateParamNames == params:
                        return [scope]
                return []

        # Try looking up the base entity
        # and then resolve from there.
        pathParts = pathPart.split(".")
        if len(pathParts) > 1:
            base = pathParts[0]
            for e in self.name_to_entities.get(base, []):
                # Several entities can have the same name,
                # especially considering that constructors have the same name as their class.
                assert e.name == base
                resolved = resolveLocal(e, pathParts[1:], paramPart)
                candidates += resolved


        candidates = list(set(candidates))
        pathCandidates = candidates

        if paramPart is not None:
            candidateParamNames = [",".join(param.typename for param in params_for_entity(cand)) for cand in candidates]
            candidates = [c for c, paramNames in zip(candidates, candidateParamNames) if paramNames == paramPart]

        if resolve_scope is not None:
            candidates += resolveLocal(resolve_scope, pathPart.split("."), paramPart)

        # Remove duplicates
        candidates = list(dict.fromkeys(candidates))

        def entity_fullname(e: Entity) -> str:
            if type(e) is MemberEntity:
                params = params_for_entity(e)
                suffix = [e.kind]
                if e.explicit_interface_implementation:
                    suffix.append("explicit interface implementation")
                return e.full_canonical_path() + ("(" + ",".join(param.typename for param in params) + ")" if len(params) > 0 else "") + f" ({', '.join(suffix)})"
            else:
                return e.full_canonical_path() + " (" + (e.kind if e.kind is not None else "<no kind>") + ")"


        if len(candidates) == 0:
            print()
            print("Could not find any entity with the name '" + name + "'. ")
            if resolve_scope is not None:
                print(f"When generating documentation for {resolve_scope.full_canonical_path()} {resolve_scope.kind}")
            if len(pathCandidates) > 0:
                print("There were some entities that matched the name but not the parameter list. The candidates are:")
                for cand in pathCandidates:
                    fullname = entity_fullname(cand)
                    print(fullname)
            else:
                name_matching = self.name_to_entities.get(pathParts[-1], [])
                if len(name_matching) > 0:
                    print("There were some entities that matched the name but not the path. The candidates are:")
                    for e in name_matching:
                        print(e.full_canonical_path() + " (" + e.kind + ")")

            return None

        def tree_distance_inheritance(entity: Entity, resolve_scope: Entity) -> float:
            if entity == resolve_scope:
                return 0
            if isinstance(entity, ClassEntity) and entity.parent == resolve_scope:
                return 0
            if isinstance(entity, NamespaceEntity) and entity.parent_namespace == resolve_scope:
                return 0
            if isinstance(entity, MemberEntity) and entity.defined_in_entity == resolve_scope:
                return 0

            if isinstance(resolve_scope, ClassEntity):
                # Check if the entity is inherited
                for base in resolve_scope.inherits_from:
                    if base.entity is not None:
                        return 1 + tree_distance_inheritance(entity, base.entity)

            return float('inf')

        def tree_distance_path(entity: Entity, resolve_scope: Entity) -> int:
            ancestors = resolve_scope.full_canonical_path_list()
            dist = 0
            while entity is not None:
                if entity in ancestors:
                    return dist + (len(ancestors) - 1 - ancestors.index(entity))
                entity = entity.parent_in_canonical_path()
                dist += 1

            return dist + len(ancestors)

        if resolve_scope is not None:
            try:
                prev_cands = candidates
                candidates = [(tree_distance_inheritance(c, resolve_scope), c) for c in candidates]
                # Sort by score and pick only the candidates with the lowest score
                candidates.sort(key=lambda x: x[0])
                new_candidates = [c[1] for c in candidates if c[0] == candidates[0][0]]
                if debug:
                    if len(prev_cands) != len(new_candidates):
                        print("Resolved to a different entity based on inheritance " + name + " in " + resolve_scope.full_canonical_path())
                        print("Previous candidates:")
                        for cand in prev_cands:
                            print(entity_fullname(cand))
                        print("New candidates:")
                        for (s, cand) in candidates:
                            print(entity_fullname(cand) + ": " + str(s))
                        print()

                candidates = new_candidates

                candidates = [(tree_distance_path(c, resolve_scope), c) for c in candidates]
                # Sort by score and pick only the candidates with the lowest score
                candidates.sort(key=lambda x: x[0])
                candidates = [c[1] for c in candidates if c[0] == candidates[0][0]]
            except Exception as e:
                print(e)
                exit(0)

        # If we specify parameters explicitly we shouldn't link to an overload page
        if paramPart is not None or ignore_overloads:
            candidates = [c for c in candidates if not isinstance(c, OverloadEntity)]

        if len(candidates) > 1:
            # Check if all of them are in the same overload group
            groups = [e for e in self.entities if isinstance(e, OverloadEntity) \
                and all(c == e or c in e.inner_members for c in candidates)
            ]

            # groups = [c for c in candidates if isinstance(c, OverloadEntity)]
            if len(groups) == 1:
                group = groups[0]
                if len(group.inner_members) == 1:
                    # If the overload group only has 1 member, return that instead
                    candidates = [group.inner_members[0]]
                else:
                    candidates = [group]

        if len(candidates) > 1 and paramPart is None:
            # Check if we have both an object and its constructor.
            # In that case prioritize the object
            groups = [c for c in candidates if isinstance(c, ClassEntity)]
            if len(groups) == 1:
                group = groups[0]
                if all(c == group or c.parent_in_canonical_path() == group for c in candidates):
                    candidates = [group]

        if kind_filter is not None:
            orig = candidates
            candidates = [c for c in candidates if c.kind == kind_filter]
            if len(candidates) == 0:
                print()
                print(f"Could not find any entity with the name '{name}' and kind filter {kind_filter}.")
                if resolve_scope is not None:
                    print(f"When generating documentation for {resolve_scope.full_canonical_path()} {resolve_scope.kind}")

                if len(orig) > 0:
                    print("The kind filter removed {len(orig)} items that would otherwise match.")

                return None

        if len(candidates) > 1:
            # In some cases we can have multiple candiates, but of which some don't actually match the full canonical path.
            # In that case we should prefer the one that matches the full canonical path.
            # This can happen for example in this case:
            #
            # Ambigious reference 'RichAI.rotation' in a tag.2 entities match this name.
            # When generating documentation for Tutorials.Changelog
            # The matching candidates are
            # Pathfinding.RichAI.rotation (property)
            # Pathfinding.AIBase.rotation (property)
            #
            # where one is an inherited member, and one is an explicit interface implementation.
            strictMatches = [c for c in candidates if pathPart in c.full_canonical_path()]
            if len(strictMatches) == 1:
                candidates = strictMatches

        if len(candidates) > 1:
            # If some of the candidates are explicit interface implementations, avoid those
            # since they are not very useful to link to.
            nonExplicitInterfaceImplementations = [c for c in candidates if not (isinstance(c, MemberEntity) and c.explicit_interface_implementation)]
            if len(nonExplicitInterfaceImplementations) >= 1 and len(nonExplicitInterfaceImplementations) < len(candidates):
                candidates = nonExplicitInterfaceImplementations

        if len(candidates) > 1:
            print()
            print(f"Ambigious reference '{name}'. {len(candidates)} entities match this name.")
            if resolve_scope is not None:
                print(f"When generating documentation for {resolve_scope.full_canonical_path()}")

            print("The matching candidates are")
            for cand in candidates:
                fullname = entity_fullname(cand)
                print(fullname)
            return None

        return candidates[0]



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
