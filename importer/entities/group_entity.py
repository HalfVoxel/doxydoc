from .entity import Entity


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
