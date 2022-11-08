import re
from typing import Callable, List, TYPE_CHECKING
from importer.entities import Entity, MemberEntity
from importer import Importer
from .settings import Settings
import copy
import jinja2

if TYPE_CHECKING:
    from builder.page import Page


class WritingContext:
    def __init__(self, state: Importer, settings: Settings, jinja_environment: jinja2.Environment) -> None:
        assert state is not None
        self.state = state
        self.settings = settings
        self.strip_links = False
        self.page: Page = None
        self.entity_scope: Entity = None
        self.sort_entities: Callable[[List[Entity]],List[Entity]] = None
        self.jinja_environment = jinja_environment
        self.exclude_regexes = [re.compile(r) for r in settings.should_exclude_entity_in_output]
        self.exclude_cache = {}

        # Function mapping paths to paths relative to the current page
        # Set by the page generator
        self.relpath = None  # type: Callable[[str],str]

    def with_link_stripping(self) -> 'WritingContext':
        ctx = copy.copy(self)
        ctx.strip_links = True
        return ctx

    def getref(self, xml) -> Entity:
        return self.state.ctx.getref(xml)

    def getref_from_name(self, name: str):
        return self.state.getref_from_name(name, self.entity_scope)
    
    def is_entity_excluded(self, e: Entity) -> bool:
        assert isinstance(e, Entity)
        if e in self.exclude_cache:
            return self.exclude_cache[e]
        res = False
        for r in self.exclude_regexes:
            if r.search(e.full_canonical_path()) is not None:
                res = True
        self.exclude_cache[e] = res
        return res
