class Location:
    def __init__(self):
        self.file = None  # type: str
        self.line = 0  # type: int
        self.column = 0  # type: int
        self.body_file = None  # type: str
        self.body_start_line = 0  # type: int
        self.body_end_line = 0  # type: int

    def read_from_xml(self, xml):
        self.file = xml.get("file")
        self.line = xml.get("line")
        self.column = xml.get("column")
        self.body_file = xml.get("bodyfile")
        self.body_start_line = xml.get("bodystart")
        self.body_end_line = xml.get("bodyend")
