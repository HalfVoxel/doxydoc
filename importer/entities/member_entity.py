import re
from .entity import Entity
from importer.protection import Protection


class MemberEntity(Entity):
    def __init__(self):
        super().__init__()

        self.protection = Protection()

        self.virtual = False
        self.static = False

        self.reimplementedby = []

        self.reimplements = []

        # TODO: Rename to overrides
        self.override = None

        # TODO: What is this?
        self.initializer = None

        self.type = None

        self.readonly = False

        # TODO: Remove?
        self.members = []

        # TODO: Remove?
        self.all_members = []

        self.argsstring = None

        # TODO: Remove?
        self.hasparams = False
        self.params = []

        self.paramdescs = []

        # ClassEntity probably
        self.defined_in_entity = None

    def read_from_xml(self):
        super().read_from_xml()
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

        self.reimplementedby = [node.get("ref") for node in xml.findall("reimplementedby")]
        self.reimplements = [node.get("ref") for node in xml.findall("reimplements")]

        override = len(self.reimplements) > 0 and self.virtual == "virtual"

        if override:
            assert xml.find("definition").text
            types = xml.find("definition").text.split()
            override_type = None
            if "override" in types:
                override_type = "override"
            if "new" in types:
                # print (types, override_type, self.id)
                assert(override_type is None)
                override_type = "new"

            override = override_type

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
                self.type.text = re.sub(override_pattern, "", self.type.text, 1)
        else:
            self.type = None
            self.readonly = False

            self.members = [node.get("docobj") for node in xml.findall("enumvalue")]
            # TODO Need to set val.set("kind", "enumvalue") on the children during read_xml
            # for val in vals:
            #     # Doxygen does not set the kind for these members
            #     # so we set it here for simplicity
            #     val.set("kind", "enumvalue")
            #     gather_member_doc(val)
            #     self.members.append(val.get("docobj"))

            # Only one members list
            self.all_members = self.members

        # Parse(function) arguments
        argsstring = xml.find("argsstring")
        # Test if this member has arguments(.text will be None if the tag is empty)
        if argsstring is not None and argsstring.text is not None:
            self.argsstring = argsstring.text

            self.hasparams = True
            params = xml.findall("param")
            self.params = []
            for param in params:
                o = Entity()
                o.xml = param
                o.name = param.find("declname").text
                o.type = param.find("type")

                # Description will be filled in later if found
                o.description = None
                self.params.append(o)
        else:
            self.hasparams = False
            self.params = []

        if self.detaileddescription is not None:
            paramdescs = self.detaileddescription.findall(".//parameterlist")
            self.paramdescs = []

            # TODO, Take care of 'Exception' "parameters"

            for pd in paramdescs:
                # kind = pd.get("kind")
                # Note use 'kind'

                # Note, should be just a simple object
                o = Entity()
                o.names = []
                o.description = None

                for n in pd:
                    names = n.findall("parameternamelist")
                    o.description = n.find("parameterdescription")
                    if names is not None:
                        for name in names:
                            o.names.append(name.text)
                            # Note use direction and type

                self.paramdescs.append(o)

            if self.params is None and len(self.paramdescs) > 0:
                print("Wait wut " + self.defined_in_entity.name + "::" + self.name)

            # Set descriptions on the parameter objects
            for pd in self.paramdescs:
                for name in pd.names:
                    for p in self.params:
                        if p.name == name:
                            p.description = pd.description
                            print("Found matching parameter " + p.name)
                            break

        # Depending on settings, this object be hidden
        # If .hidden is true, no links to it will be generated, instead just plain text
        # TODO: Should not be set in the read_xml method
        # self.hidden = is_detail_hidden(self)
