from .entity import Entity, gather_members
from importer.protection import Protection


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
