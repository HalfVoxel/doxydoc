from .entity import Entity, gather_members


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
