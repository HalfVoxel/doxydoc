import re
from .entity import Entity
from .param_entity import ParamEntity
from .enum_value_entity import EnumValueEntity
from importer.protection import Protection
from typing import Dict, List, Optional, TYPE_CHECKING
import xml.etree.ElementTree as ET
from importer.importer_context import ImporterContext

if TYPE_CHECKING:
    from importer import Importer


class MemberEntity(Entity):
    def __repr__(self) -> str:
        return "<entity name=" + self.name + " id=" + self.id + ">"

    def __init__(self) -> None:
        super().__init__()

        # TODO: Use Protection class
        self.protection = None  # type: str

        self.virtual = None  # type: str
        self.static = False

        self.reimplementedby = []  # type: List[Entity]

        self.reimplements = []  # type: List[Entity]

        # TODO: Rename to overrides
        self.override = None  # type: str

        ''' The value the member is initialized to '''
        self.initializer = None  # type: ET.Element

        self.type = None  # type: ET.Element

        self.readonly = False

        self.abstract = False  # type: bool

        # Contains enum values if this is an enum
        self.members = []  # type: List[Entity]

        # Remove?
        self.all_members = []  # type: List[Entity]

        self.argsstring = None  # type: str

        # TODO: Remove?
        self.hasparams = False
        self.params = []  # type: List[ParamEntity]

        # ClassEntity probably
        self.defined_in_entity = None  # type: Entity

    def get_simple_type(self, ctx: ImporterContext) -> Optional[Entity]:
        '''
        Returns the entity corresponding to the member's type if it is a simple type.
        E.g. WhateverClass, but for List<Whatever> it returns None.
        It also returns None if there is no corresponding entity, e.g. a primitive type like float.
        '''
        # For enum members the type is None
        if self.type is None:
            return None

        children = list(self.type)
        if len(children) == 1:
            if children[0].tag == "ref":
                return ctx.getref(children[0])
        return None

    def child_entities(self):
        return self.members  # ??

    def parent_in_canonical_path(self) -> Entity:
        return self.defined_in_entity

    def read_from_xml(self, ctx: ImporterContext) -> None:
        super().read_from_xml(ctx)
        xml = self.xml

        # xml
        # id
        # name
        # kind
        # protection
        # virtual
        # static
        # override
        # readonly
        # reimplements
        # reimplementedby
        # briefdesc
        # detaileddesc
        # type

        prot = xml.get("prot")
        if prot is not None:
            self.protection = prot
        else:
            self.protection = None

        virt = xml.get("virt")
        if virt is not None and virt != "non-virtual":
            self.virtual = virt
        else:
            self.virtual = None

        self.static = xml.get("static") == "yes"

        self.reimplementedby = [ctx.getref(node) for node in xml.findall("reimplementedby")]
        self.reimplements = [ctx.getref(node) for node in xml.findall("reimplements")]

        override = len(self.reimplements) > 0 and self.virtual == "virtual"

        definition = xml.find("definition")

        if definition is not None:
            self.abstract = "abstract" in definition.text.split()

        if override:
            assert definition.text
            types = definition.text.split()
            override_type = None
            if "override" in types:
                override_type = "override"
            if "new" in types:
                # print (types, override_type, self.id)
                assert(override_type is None)
                override_type = "new"

            # For abstract classes or interfaces, it might reimplement some function
            # without overriding it thus the need to check again here
            self.override = override_type
        else:
            self.override = None

        self.initializer = xml.find("initializer")

        if self.kind != "enum":
            # Find type
            # TODO: no XML items here
            self.type = xml.find("type")

            # Is the xml read only.
            # Doxygen will put 'readonly' at the start of the 'type' field if it is readonly
            self.readonly = (
                self.type is not None and
                self.type.text is not None and
                "readonly " in self.type.text
            )

            if self.type is not None and self.type.text is not None:
                # Remove eventual 'override ' text at start of type.
                override_pattern = "(?:override|new|readonly|abstract)\s"
                self.type.text = re.sub(override_pattern, "", str(self.type.text), 1)
        else:
            self.type = None
            self.readonly = False

            self.members = []
            for v in xml.findall("enumvalue"):
                enumvalue = EnumValueEntity()
                enumvalue.xml = v
                enumvalue.read_from_xml(ctx)
                # This is not set in the xml
                enumvalue.kind = "enumvalue"
                self.members.append(enumvalue)
                ctx.setentity(v, enumvalue)

            # Only one members list
            self.all_members = self.members

        # Parse(function) arguments
        argsstring = xml.find("argsstring")
        # Test if this member has arguments(.text will be None if the tag is empty)
        if argsstring is not None and argsstring.text is not None:
            self.argsstring = str(argsstring.text)

            self.hasparams = True
            params = xml.findall("param")
            self.params = []
            for param in params:
                o = ParamEntity()
                o.xml = param
                o.read_from_xml(ctx)
                self.params.append(o)
        else:
            self.hasparams = False
            self.params = []

    def post_xml_read(self, state: 'Importer') -> None:
        super().post_xml_read(state)
        if self.detaileddescription is not None:
            paramdescs = self.detaileddescription.findall(".//parameterlist")
            for parameterList in paramdescs:
                for parameterItem in parameterList:
                    # kind = parameterItem.get("kind")
                    # Note use 'kind'

                    nameLists = parameterItem.findall("parameternamelist")
                    description = parameterItem.find("parameterdescription")
                    names = []  # type: List[str]
                    for ls in nameLists:
                        names += [str(name.text) for name in ls]

                    # TODO use direction and type

                    # Set descriptions on the parameter objects
                    for name in names:
                        for p in self.params:
                            if p.name == name:
                                p.detaileddescription = description
                                break

        # Depending on settings, this object be hidden
        # If .hidden is true, no links to it will be generated, instead just plain text
        # TODO: Should not be set in the read_xml method
        # self.hidden = is_detail_hidden(self)
