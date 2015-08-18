from pprint import pprint
from xml.sax.saxutils import escape
from doxysettings import DocSettings
from writing_context import WritingContext
import jinja2
import re

FILE_EXT = ".html"
OUTPUT_DIR = "html"

docobjs = {}

# escape() and unescape() takes care of &, < and >.
html_escape_table = {
    '"': "&quot;",
    "'": "&apos;"
}
html_unescape_table = {v: k for k, v in html_escape_table.items()}


def paramescape(v):
    return escape(v, html_escape_table)


class JinjaFilter:
    def __init__(self, f):
        print ("Warning: Jinja filters are not functional yet")


class DocState:

    def __init__(self):
        self.currentobj = None
        self.navitems = []

        self.pages = []
        self.roots = None
        self.input_xml = None
        self.environment = None
        self._filters = []
        self.entities = []

        ''' Prevents infinte loops of tooltips in links by disabling links after a certain depth '''
        self.depth_ref = 0

        self._docobjs = {}

        self._trigger_heaps = {}

        self._usedPaths = set()

    def add_filter(self, name, func):
        self._filters.append((name, func))

    def create_template_env(self, dir, filters):
        self.environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(dir),
            line_statement_prefix="#", line_comment_prefix="##"
        )

        for key, fun in filters.items():
            def wrapper(args):
                return str(fun(args, WritingContext(self)))

            self.environment.filters[key] = wrapper

    def iter_unique_docobjs(self):
        for k, v in self._docobjs.items():
            if k == v.id:
                yield v

    def add_docobj(self, obj, id=None):
        if id is None:
            id = obj.id
        self._docobjs[id] = obj
        # Workaround for doxygen apparently generating refid:s which do not exist as id:s
        id2 = obj.id + "_1" + obj.id
        self._docobjs[id2] = obj
        self.entities.append(obj)

    def has_docobj(self, id):
        return id in self._docobjs

    def get_docobj(self, id):
        return self._docobjs[id]

    def trigger_listener(self, name, priority, callback):
        assert callback
        assert name

        if DocSettings.args.verbose:
            print ("Adding listener for " + name + " with priority " + priority)

        if name not in self._trigger_heaps:
            self._trigger_heaps[name] = []

        self._trigger_heaps[name].append((priority, callback))
        self._trigger_heaps[name].sort(key=lambda tup: tup[0])

    def trigger(self, name):

        if name not in self._trigger_heaps:
            return

        events = self._trigger_heaps[name]

        for event in events:
            event[1]()

    ''' Register a page with a docobj and xml node.
        Assumed to be a node in a previously found compound xml file
    '''
    def register_page(self, obj, xml):
        obj.path = obj.name.replace("::", "-")
        obj.anchor = None

        self.pages.append(obj)

        counter = 1
        while (obj.path + ("" if counter == 1 else str(counter))) in self._usedPaths:
            counter += 1

        if counter > 1:
            obj.path = obj.path + str(counter)

        self._usedPaths.add(obj.path)

        self.add_docobj(obj)

        ids = xml.findall(".//*[@id]")

        parent = obj

        # Set all child nodes to refer to this page instead of the original page
        for idnode in ids:

            obj = idnode.get("docobj")

            if obj is not None:
                obj.compound = parent

    def create_entity(self, xml):
        kind = xml.get("kind")

        if kind == "class" or kind == "struct" or kind == "interface":
            entity = ClassEntity()
        elif kind == "file":
            entity = FileEntity()
        elif kind == "namespace":
            entity = NamespaceEntity()
        elif kind == "group":
            entity = GroupEntity()
        elif kind == "page":
            entity = PageEntity()
        elif kind == "example":
            entity = ExampleEntity()
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
            entity = MemberEntity()
        elif (kind == "union" or
                kind == "protocol" or
                kind == "category" or
                kind == "exception" or
                kind == "dir"):
            # Unsupported known entity type
            entity = Entity()
        elif kind is None and "sect" in xml.tag:
            # Valid for things like sect[1-4]
            entity = SectEntity()
        else:
            print("Unexpected kind: " + kind)
            entity = Entity()

        entity.xml = xml
        entity.read_base_xml()

        if entity.id == "":
            print ("Warning: Found an entity without an ID. Skipping")
            return None

        self.add_docobj(entity)
        xml.set("docobj", entity)
        return entity

    def register_compound(self, xml):

        entity = self.create_entity(xml)

        # TODO: Separate page class
        self.pages.append(entity)

        # Will only be used for debugging if even that. Formatted name will be added later
        entity.name = xml.find("compoundname").text

        memberdefs = xml.findall("sectiondef/memberdef")
        for member in memberdefs:
            self.create_entity(member)

        # Find sect[1-4]
        sects = (xml.findall(".//sect1") +
                 xml.findall(".//sect2") +
                 xml.findall(".//sect3") +
                 xml.findall(".//sect4"))

        for sect in sects:
            entity = self.create_entity(sect)

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
        #         self.add_docobj(entity)
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


class EntityPath:
    def __init__(self):
        self.path = None
        self.anchor = None
        self.parent = None
        self.page = None

    def full_url(self):
        ''' Url to the page (including possible anchor) where the Entity exists '''

        url = self.page_url()
        if self.anchor is not None:
            url += "#" + self.anchor
        return url

    def page_url(self):
        ''' Url to the page where the Entity exists '''

        if hasattr(self, 'exturl'):
            return self.exturl

        if self.path is not None:
            url = self.path
        else:
            if self.parent is not None:
                url = self.parent.page_url()
            else:
                print("NO COMPOUND ON OBJECT WITHOUT PATH")
                dump(self)
                url = "<undefined>"

        return url

    def full_path(self):
        ''' Path to the file which contains this Entity '''

        if self.path is not None:
            url = self.path
        else:
            if self.parent is not None:
                url = self.parent.full_url()
            else:
                print("NO COMPOUND ON OBJECT WITHOUT PATH")
                dump(self)
                url = "<undefined>"

        return OUTPUT_DIR + "/" + url


class Entity:
    def __init__(self):
        self.hidden = False
        self.name = ""
        self.briefdescription = None
        self.detaileddescription = None
        self.id = ""
        self.path = EntityPath()
        self.xml = None

        # Sections in descriptions that can be linked to
        self.sections = []

    def __str__(self):
        return "Entity: " + self.id

    @staticmethod
    def formatname(name):
        return name.replace("::", ".")

    def read_base_xml(self):
        self.id = self.xml.get("id")
        self.kind = self.xml.get("kind")

    def read_from_xml(self):
        xml = self.xml

        if xml is None:
            print("XML is None on " + self.id + " " + self.kind)
        name_node = xml.find("title")
        if name_node is None:
            name_node = xml.find("compoundname")
        if name_node is None:
            name_node = xml.find("name")

        if name_node is not None:
            self.name = Entity.formatname(name_node.text)
        else:
            self.name = "#" + self.kind + "#"

        self.briefdescription = xml.find("briefdescription")
        self.detaileddescription = xml.find("detaileddescription")

        # Find sections
        # TODO: Optimize
        section_xml = []
        if self.briefdescription is not None:
            section_xml = (section_xml +
                           self.briefdescription.findall(".//sect1") +
                           self.briefdescription.findall(".//sect2") +
                           self.briefdescription.findall(".//sect3") +
                           self.briefdescription.findall(".//sect4"))

        if self.detaileddescription is not None:
            section_xml = (section_xml +
                           self.detaileddescription.findall(".//sect1") +
                           self.detaileddescription.findall(".//sect2") +
                           self.detaileddescription.findall(".//sect3") +
                           self.detaileddescription.findall(".//sect4"))

        self.sections = [sec.get("docobj") for sec in section_xml if sec.get("docobj") is not None]


class GroupEntity(Entity):
    def __init__(self):
        super().__init__()
        self.innerclasses = []
        self.innernamespaces = []
        self.innergroups = []

    def read_from_xml(self):
        super().read_from_xml()
        xml = self.xml

        self.title = Entity.formatname(xml.find("title").text)

        self.innerclasses = [node.get("ref") for node in xml.findall("innerclass")]
        self.innernamespaces = [node.get("ref") for node in xml.findall("innernamespace")]

        self.innergroups = [node.get("ref") for node in xml.findall("innergroup")]


class ExampleEntity(Entity):
    pass


def gather_members(xml):
    return [memberdef.get("docobj") for memberdef in xml.findall("sectiondef/memberdef")]


class FileEntity(Entity):
    def __init__(self):
        super().__init__()

        self.innerclasses = []
        self.innernamespaces = []
        self.contents = None
        self.location = None  # TODO: Unknown location
        # TODO gather_members

    def read_from_xml(self):
        super().read_from_xml()
        xml = self.xml

        self.innerclasses = [node.get("ref") for node in xml.findall("innerclass")]
        self.innernamespaces = [node.get("ref") for node in xml.findall("innernamespace")]

        self.contents = xml.find("programlisting")

        self.members = gather_members(xml)
        # Only one members list
        self.all_members = self.members

        # Find location of file
        loc = xml.find("location")
        self.location = loc.get("file") if loc is not None else None


class Protection:
    def __init__(self):
        self.final = False
        self.sealed = False
        self.abstract = False


class ClassEntity(Entity):
    def __init__(self):
        super().__init__()

        self.protection = Protection()
        self.inherited = []
        self.derived = []
        self.members = []
        self.all_members = []

        # TODO gather_members

    def read_from_xml(self):
        super().read_from_xml()
        xml = self.xml

        self.protection = xml.get("prot")
        self.members = gather_members(xml)

        self.briefdescription = xml.find("briefdescription")
        self.detaileddescription = xml.find("detaileddescription")

        self.final = xml.get("final") == "yes"
        self.sealed = xml.get("sealed") == "yes"
        self.abstract = xml.get("abstract") == "yes"

        self.inherited = [node.get("ref") for node in xml.findall("basecompoundref")]
        self.derived = [node.get("ref") for node in xml.findall("derivedcompoundref")]

        # All members, also inherited ones
        self.all_members = [m.get("ref") for m in xml.find("listofallmembers")]
        for m in xml.find("listofallmembers"):
            if m.get("ref") is None:
                print ("NULL REFERENCE " + m.find("name").text + " " + m.find("scope").text)
                print ("Sure not old files are in the xml directory")


class PageEntity(Entity):
    def __init__(self):
        super().__init__()

        self.subpages = []

        # TODO: Why subpages AND innerpages?
        self.innerpages = []

    def read_from_xml(self):
        super().read_from_xml()
        xml = self.xml

        # xml
        # id
        # name
        # kind
        # briefdesc
        # detaileddesc
        # innerpage

        title = xml.find("title")
        if title is not None and title.text is not None:
            self.name = Entity.formatname(title.text)
        else:
            self.name = ""

        self.subpages = [node.get("ref") for node in xml.findall("innerpage")]
        for p in self.subpages:
            p.parentpage = self

        self.innerpages = self.subpages


class NamespaceEntity(Entity):
    def __init__(self):
        super().__init__()

        self.innerclasses = []
        self.innernamespaces = []

    def read_from_xml(self):
        super().read_from_xml()
        xml = self.xml

        self.innerclasses = [node.get("ref") for node in xml.findall("innerclass")]
        self.innernamespaces = [node.get("ref") for node in xml.findall("innernamespaces")]
        self.members = gather_members(xml)


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
                print("Wait wut " + DocState.compound.name + "::" + self.name)

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


class ExternalEntity(Entity):
    def read_from_xml(self):
        # Nothing to read since this
        # entity is not based on an XML file
        pass


class SectEntity(Entity):
    def read_from_xml(self):
        title = self.xml.find("title")
        self.name = Entity.formatname(title.text)


def dump(obj):
    pprint(vars(obj))

# Cannot add as decorator since the DocState class is not defined at function definition time
JinjaFilter(DocState.trigger)

# Sort navitems before build
# TODO!!
# DocState.add_event(2500, lambda: DocState.navitems.sort(key=lambda v: v.order))
