from typing import Callable
from importer.entities import Entity
from importer import Importer
from .settings import Settings


class WritingContext:
    def __init__(self, state: Importer, settings: Settings) -> None:
        assert state is not None
        self.state = state
        self.settings = settings
        self.strip_links = False

        # Function mapping paths to paths relative to the current page
        # Set by the page generator
        self.relpath = None  # type: Callable[[str],str]

    def with_link_stripping(self) -> 'WritingContext':
        ctx = WritingContext(self.state, self.settings)
        ctx.strip_links = True
        return ctx

    def getref(self, xml) -> Entity:
        return self.state.ctx.getref(xml)
