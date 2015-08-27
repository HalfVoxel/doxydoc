from .entity import Entity


class SectEntity(Entity):
    def read_from_xml(self):
        title = self.xml.find("title")
        self.name = Entity.formatname(title.text)
