class Settings:
    def __init__(self):
        self.external = {}
        self.hide_undocumented = True
        self.show_member_protection_in_list = True
        self.show_member_type_in_list = True
        self.show_source_files = True
        self.show_file_paths = True
        self.keep_empty_member_sections = False
        self.args = None
        self.out_dir = "html"
        self.template_dirs = ["templates"]
        self.flat_file_hierarchy = False
