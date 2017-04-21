from pprint import pprint
from importer.entities import Entity
from typing import List, Tuple


def dump(obj):
    pprint(vars(obj))


def get_member_sections(entity: Entity, members: List[Entity]) -> List[Tuple[str, List[Entity]]]:
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

    # Partition the members into different sections using lambdas
    section_spec = [
        (lambda m: m.protection == "public" and m.defined_in_entity == entity, [
            ("Public Methods", lambda m: not m.static and m.kind == "function"),
            ("Public Static Methods", lambda m: m.static and m.kind == "function"),
            ("Public Properties", lambda m: not m.static and m.kind == "property"),
            ("Public Static Properties", lambda m: m.static and m.kind == "property"),
            ("Public Variables", lambda m: not m.static and m.kind == "variable"),
            ("Public Static Variables", lambda m: m.static and m.kind == "variable"),
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
        (lambda m: True, [
            ("Private/Protected Members", lambda m: m.protection != "public" and m.defined_in_entity == entity),
            ("Inherited Members", lambda m: m.defined_in_entity != entity),
        ])
    ]

    sections = []
    for outer in section_spec:
        filtered = list(filter(outer[0], members))
        for s in outer[1]:
            sections.append((s[0], list(filter(s[1], filtered))))

    return sections
