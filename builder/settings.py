from typing import Any


class Settings:
    def __init__(self, settings_dict) -> None:
        self.hide_undocumented = True
        self.show_member_protection_in_list = True
        self.show_member_type_in_list = True
        self.show_source_files = True
        self.show_file_paths = True
        self.keep_empty_member_sections = False
        self.args = None  # type: Any
        self.out_dir = "html"
        self.template_dirs = ["templates"]
        self.title = "Project Title"
        self.version = "0.1"
        self.flat_file_hierarchy = False
        self.disabled_plugins = []  # type: List[str]
        self.page_whitelist = None  # type: List[str]
        self.absolute_url_base = None  # type: str
        self.plugins = None  # type: Dict[Any]

        if settings_dict is not None:
            for k, v in settings_dict.items():
                if hasattr(self, k):
                    setattr(self, k, v)
                else:
                    raise Exception("Unknown config parameter '" + k + "'")
