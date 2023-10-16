from typing import Any, List, Dict, Optional
import os
from dataclasses import dataclass


class Settings:
    hide_undocumented: bool = True
    show_member_protection_in_list: bool = True
    show_member_type_in_list: bool = True
    show_source_files: bool = True
    show_file_paths: bool = True
    keep_empty_member_sections: bool = False
    args: Any = None
    in_dir: str = "input"
    out_dir: str = "html"
    branch: Optional[str] = None
    is_beta: bool = False
    template_dirs: List[str] = ["templates"]
    title: str = "Project Title"
    version: str = "0.1"
    flat_file_hierarchy: bool = False
    disabled_plugins: List[str] = []
    page_whitelist: Optional[List[str]] = None
    absolute_url_base: Optional[str] = None
    documentation_collection_base_url: Optional[str] = None
    banner: Optional[str] = None
    breadcrumbs: bool = True
    plugins: Optional[Dict[str,Any]] = None
    doxygen_redirects: bool = False
    doxygen_redirect_extension: str = ".html"
    extra_css: Optional[str] = None
    links_in_code_blocks = True
    separate_function_pages: bool = True
    should_exclude_entity_in_output: List[str] = []
    
    def __init__(self, settings_dict, paths_relative_to: str) -> None:
        if settings_dict is not None:
            for k, v in settings_dict.items():
                if hasattr(self, k):
                    setattr(self, k, v)
                else:
                    raise Exception("Unknown config parameter '" + k + "'")

        self.in_dir = os.path.join(paths_relative_to, self.in_dir) if self.in_dir else self.in_dir
        self.out_dir = os.path.join(paths_relative_to, self.out_dir) if self.out_dir else self.out_dir
        self.extra_css = os.path.join(paths_relative_to, self.extra_css) if self.extra_css else self.extra_css
