from pprint import pprint


def dump(obj):
    pprint(vars(obj))


def get_member_sections(entity, members):
    ''' Returns a list of sections in which to group members for display '''
    sections = []

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

    our_methods = [m for m in members if m.defined_in_entity == entity]
    instance_methods = [m for m in our_methods if not m.static]
    static_methods = [m for m in our_methods if m.static]

    public_instance_methods = [m for m in instance_methods if m.protection == "public"]
    public_static_methods = [m for m in static_methods if m.protection == "public"]

    sections.append((
        "Public Methods",
        [m for m in public_instance_methods if m.kind == "function"]
    ))
    sections.append((
        "Public Properties",
        [m for m in public_instance_methods if m.kind == "property"]
    ))
    sections.append((
        "Public Variables",
        [m for m in public_instance_methods if m.kind == "variable"]
    ))
    sections.append((
        "Public Events",
        [m for m in public_instance_methods if m.kind == "event"]
    ))
    sections.append((
        "Public Typedefs",
        [m for m in public_instance_methods if m.kind == "typedef"]
    ))
    sections.append((
        "Public Signals",
        [m for m in public_instance_methods if m.kind == "signal"]
    ))
    sections.append((
        "Public Prototypes",
        [m for m in public_instance_methods if m.kind == "prototype"]
    ))
    sections.append((
        "Public Friends",
        [m for m in public_instance_methods if m.kind == "friend"]
    ))
    sections.append((
        "Public Slots",
        [m for m in public_instance_methods if m.kind == "slot"]
    ))

    sections.append((
        "Public Static Methods",
        [m for m in public_static_methods if m.kind == "function"]
    ))
    sections.append((
        "Public Static Properties",
        [m for m in public_static_methods if m.kind == "property"]
    ))
    sections.append((
        "Public Static Variables",
        [m for m in public_static_methods if m.kind == "variable"]
    ))
    sections.append((
        "Public Static Events",
        [m for m in public_static_methods if m.kind == "event"]
    ))
    sections.append((
        "Public Static Typedefs",
        [m for m in public_static_methods if m.kind == "typedef"]
    ))
    sections.append((
        "Public Static Signals",
        [m for m in public_static_methods if m.kind == "signal"]
    ))
    sections.append((
        "Public Static Prototypes",
        [m for m in public_static_methods if m.kind == "prototype"]
    ))
    sections.append((
        "Public Static Friends",
        [m for m in public_static_methods if m.kind == "friend"]
    ))
    sections.append((
        "Public Static Slots",
        [m for m in public_static_methods if m.kind == "slot"]
    ))

    sections.append((
        "Private/Protected Members",
        [m for m in members if m.protection != "public" and m.defined_in_entity == entity]
    ))

    # Handling it specially
    # There no point explicitly showing an empty section when a class does no inherit any members
    sections.append((
        "Inherited Members",
        [m for m in members if m.defined_in_entity != entity]
    ))

    # sections.append(("All Members", members))
    return sections
