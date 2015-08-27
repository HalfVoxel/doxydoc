from .entity import Entity


class ExternalEntity(Entity):
    def read_from_xml(self):
        # Nothing to read since this
        # entity is not based on an XML file
        pass
