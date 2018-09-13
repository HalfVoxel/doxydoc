from typing import Callable
from importer.entities import Entity
from importer import Importer
from .settings import Settings
import jinja2


class WritingContext:
    def __init__(self, state: Importer, settings: Settings, jinja_environment: jinja2.Environment) -> None:
        assert state is not None
        self.state = state
        self.settings = settings
        self.strip_links = False
        self.page = None  # type: Page
        self.sort_entities = None  # type: Callable[List[Entity],List[Entity]]
        self.jinja_environment = jinja_environment

        # Function mapping paths to paths relative to the current page
        # Set by the page generator
        self.relpath = None  # type: Callable[[str],str]

    def with_link_stripping(self) -> 'WritingContext':
        ctx = WritingContext(self.state, self.settings, self.jinja_environment)
        ctx.strip_links = True
        return ctx

    def getref(self, xml) -> Entity:
        return self.state.ctx.getref(xml)
