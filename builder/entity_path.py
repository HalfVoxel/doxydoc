from pprint import pprint
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .page import Page


class EntityPath:
    def __init__(self) -> None:
        self.path = None  # type: str
        self.anchor = None  # type: str
        self.parent = None  # type: EntityPath
        self.page = None  # type: Page

    def full_url(self) -> str:
        ''' Url to the page (including possible anchor) where the Entity exists '''

        url = self.page_url()
        if self.anchor is not None:
            url += "#" + self.anchor
        return url

    def page_url(self) -> str:
        ''' Url to the page where the Entity exists '''

        if hasattr(self, 'exturl'):
            return self.exturl

        if self.path is not None:
            url = self.path
        else:
            if self.parent is not None:
                url = self.parent.page_url()
            else:
                return None

        return url

    def full_path(self) -> str:
        ''' Path to the file which contains this Entity '''

        if self.path is not None:
            url = self.path
        else:
            if self.parent is not None:
                url = self.parent.full_url()
            else:
                return None

        return "todo" + "/" + url


def dump(obj) -> None:
    pprint(vars(obj))
