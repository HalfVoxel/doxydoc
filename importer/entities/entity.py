def gather_members(xml):
    return [memberdef.get("docobj") for memberdef in xml.findall("sectiondef/memberdef")]


class Entity:
    def __init__(self):
        self.hidden = False
        self.name = ""
        self.short_name = ""
        self.briefdescription = None
        self.detaileddescription = None
        self.id = ""
        self.xml = None

        # Sections in descriptions that can be linked to
        self.sections = []

    def __str__(self):
        return "Entity: " + self.id

    @staticmethod
    def formatname(name):
        return name.split("::")[-1]

    def read_base_xml(self):
        self.id = self.xml.get("id")
        self.kind = self.xml.get("kind")

    def read_from_xml(self):
        xml = self.xml

        short_name_node = xml.find("compoundname")
        name_node = xml.find("title")

        if name_node is None:
            name_node = xml.find("name")
        if name_node is None:
            name_node = short_name_node

        if short_name_node is None:
            short_name_node = name_node

        if name_node is not None and name_node.text is not None:
            self.name = Entity.formatname(name_node.text)
        else:
            self.name = "#" + self.kind + "#"

        if short_name_node is not None:
            self.short_name = Entity.formatname(short_name_node.text)
        else:
            self.short_name = "#" + self.kind + "#"

        self.briefdescription = xml.find("briefdescription")
        self.detaileddescription = xml.find("detaileddescription")

        # Find sections
        # TODO: Simplify and optimize
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
