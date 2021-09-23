from importer.main import Importer
from pprint import pprint
from importer.entities import Entity
from typing import List, Tuple
import itertools


def dump(obj):
    pprint(vars(obj))



def get_member_sections(entity: Entity, members: List[Entity], state: Importer) -> List[Tuple[str, List[Entity]]]:
    ''' Returns a list of sections in which to group members for display '''

    for m in members:
        if not hasattr(m, "protection"):
            dump(m)

# <xsd:simpleType name="DoxMemberKind">
#     <xsd:restriction base="xsd:string">
#       <xsd:enumeration value="define" />
#       <xsd:enumeration value="property" />
#       <xsd:enumeration value="event" />
#       <xsd:enumeration value="variable" />
#       <xsd:enumeration value="typedef" />
#       <xsd:enumeration value="enum" />
#       <xsd:enumeration value="function" />
#       <xsd:enumeration value="signal" />
#       <xsd:enumeration value="prototype" />
#       <xsd:enumeration value="friend" />
#       <xsd:enumeration value="dcop" />
#       <xsd:enumeration value="slot" />
#     </xsd:restriction>
#   </xsd:simpleType>
    proxied_members = []
    for ((kind, name), inner) in itertools.groupby(members, key=lambda e: (e.kind, e.name)):
        inner = list(inner)
        if kind == "function":
            overload_group_entity = state.try_get_entity(f"{entity.id}/{name}/overloads")
            if overload_group_entity is not None:
                proxied_members.append(overload_group_entity)
            else:
                proxied_members += inner
        else:
            proxied_members += inner

    # Partition the members into different sections using lambdas
    section_spec = [
        (lambda m: m.protection == "public" and m.defined_in_entity == entity and not m.deprecated, [
            ("Public Methods", lambda m: not m.static and m.kind in ["function", "function_overloads"]),
            ("Public Static Methods", lambda m: m.static and m.kind in ["function", "function_overloads"]),
            # ("Public Properties", lambda m: not m.static and m.kind == "property"),
            # ("Public Static Properties", lambda m: m.static and m.kind == "property"),
            # ("Public Variables", lambda m: not m.static and m.kind == "variable"),
            # ("Public Static Variables", lambda m: m.static and m.kind == "variable"),
            ("Public Variables", lambda m: not m.static and m.kind in ["property", "variable"]),
            ("Public Static Variables", lambda m: m.static and m.kind in ["property", "variable"]),
            ("Public Enums", lambda m: not m.static and m.kind == "enum"),
            ("Public Events", lambda m: not m.static and m.kind == "event"),
            ("Public Static Events", lambda m: m.static and m.kind == "event"),
            ("Public Typedefs", lambda m: not m.static and m.kind == "typedef"),
            ("Public Static Typedefs", lambda m: m.static and m.kind == "typedef"),
            ("Public Signals", lambda m: not m.static and m.kind == "signal"),
            ("Public Static Signals", lambda m: m.static and m.kind == "signal"),
            ("Public Prototypes", lambda m: not m.static and m.kind == "prototype"),
            ("Public Static Prototypes", lambda m: m.static and m.kind == "prototype"),
            ("Public Friends", lambda m: not m.static and m.kind == "friend"),
            ("Public Static Friends", lambda m: m.static and m.kind == "friend"),
            ("Public Slots", lambda m: not m.static and m.kind == "slot"),
            ("Public Static Slots", lambda m: m.static and m.kind == "slot"),
        ]),
        (lambda m: not m.deprecated, [
            ("Inherited Public Members", lambda m: m.defined_in_entity != entity and m.protection == "public"),
            ("Private/Protected Members", lambda m: m.protection != "public"),
        ]),
        (lambda m: m.deprecated, [
            ("Deprecated Members", lambda m: m.defined_in_entity == entity)
        ])
    ]

    sections = []
    for outer in section_spec:
        filtered = list(filter(outer[0], proxied_members))
        filtered.sort(key=lambda x: (x.name, x.location.file, x.location.line) if x.location is not None else (x.name, "", 0))
        for s in outer[1]:
            sections.append((s[0], list(filter(s[1], filtered))))

    return sections
