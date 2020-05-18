from typing import Any, List, Dict, Optional
import os


class Settings:
    def __init__(self, settings_dict, paths_relative_to: str) -> None:
        self.hide_undocumented = True
        self.show_member_protection_in_list = True
        self.show_member_type_in_list = True
        self.show_source_files = True
        self.show_file_paths = True
        self.keep_empty_member_sections = False
        self.args = None  # type: Any
        self.in_dir = "input"
        self.out_dir = "html"
        self.template_dirs = ["templates"]
        self.title = "Project Title"
        self.version = "0.1"
        self.flat_file_hierarchy = False
        self.disabled_plugins = []  # type: List[str]
        self.page_whitelist = None  # type: Optional[List[str]]
        self.absolute_url_base = None  # type: Optional[str]
        self.banner = None  # type: Optional[str]
        self.breadcrumbs = True  # type: bool
        self.plugins = None  # type: Optional[Dict[str,Any]]
        self.doxygen_redirects = False
        self.doxygen_redirect_extension = ".html"
        self.extra_css = None  # type: Optional[str]
        self.links_in_code_blocks = True

        if settings_dict is not None:
            for k, v in settings_dict.items():
                if hasattr(self, k):
                    setattr(self, k, v)
                else:
                    raise Exception("Unknown config parameter '" + k + "'")

        self.in_dir = os.path.join(paths_relative_to, self.in_dir) if self.in_dir else self.in_dir
        self.out_dir = os.path.join(paths_relative_to, self.out_dir) if self.out_dir else self.out_dir
        self.extra_css = os.path.join(paths_relative_to, self.extra_css) if self.extra_css else self.extra_css
