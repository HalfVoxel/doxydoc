from typing import Callable
from importer.entities import Entity, MemberEntity
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
        self.entity_scope: Entity = None
        self.sort_entities = None  # type: Callable[List[Entity],List[Entity]]
        self.jinja_environment = jinja_environment

        # Function mapping paths to paths relative to the current page
        # Set by the page generator
        self.relpath = None  # type: Callable[[str],str]

    def with_link_stripping(self) -> 'WritingContext':
        ctx = WritingContext(self.state, self.settings, self.jinja_environment)
        ctx.strip_links = True
        ctx.relpath = self.relpath
        ctx.page = self.page
        ctx.entity_scope = self.entity_scope
        return ctx

    def getref(self, xml) -> Entity:
        return self.state.ctx.getref(xml)

    def getref_from_name(self, name: str):
        name = name.strip()
        name = name.replace("::", ".")
        if "(" in name:
            pathPart, paramPart = name.split("(")
            pathPart = pathPart.strip()
            paramPart = paramPart.replace(" ", "").strip()

            if not paramPart.endswith(")"):
                print(f"Expected parameter list to end with a closing parenthesis: '{name}'")
                return None
            # Remove ending paren
            paramPart = paramPart[:-1]
        else:
            pathPart = name
            paramPart = ""

        candidates = []
        for entity in self.state.entities:
            name_suffix = ""
            c = entity
            while c is not None:
                name_suffix = c.name + "." + name_suffix if name_suffix != "" else c.name
                c = c.parent_in_canonical_path()
                if name_suffix == pathPart:
                    candidates.append(entity)
                    break

        pathCandidates = candidates

        def params_for_entity(entity: Entity):
            # Only member entities have parameters.
            # External entities may also be functions, but we do not know the parameters for those
            return entity.params if type(entity) is MemberEntity else []

        if paramPart != "":
            candidateParamNames = [",".join(param.typename for param in params_for_entity(cand)) for cand in candidates]
            candidates = [c for c, paramNames in zip(candidates, candidateParamNames) if paramNames == paramPart]

        if len(candidates) == 0:
            print()
            print("Could not find any entity with the name '" + name + "'.")
            if len(pathCandidates) > 0:
                print("There were some entities that matched the name but not the parameter list. The candidates are:")
                for cand in pathCandidates:
                    params = params_for_entity(cand)
                    fullname = cand.full_canonical_path() + ("(" + ",".join(param.typename for param in params) + ")" if len(params) > 0 else "")
                    print(fullname)
            return None

        def can_be_resolved_from(entity: Entity, resolve_scope: Entity):
            if type(resolve_scope) is MemberEntity:
                resolve_scope = resolve_scope.parent_in_canonical_path()

            while entity is not None:
                if entity == resolve_scope:
                    return True
                entity = entity.parent_in_canonical_path()

            return False

        if self.entity_scope is not None: 
            assert self.entity_scope is not None
            candidates = [(1 if can_be_resolved_from(c, self.entity_scope) else 0, c) for c in candidates]
            # Sort by score and pick only the candidates with the highest score
            candidates.sort(key=lambda x: x[0], reverse=True)
            candidates = [c[1] for c in candidates if c[0] == candidates[0][0]]

        if len(candidates) > 1:
            print()
            print(f"Ambigious reference '{name}' in a tag." +
                  str((len(candidates))) + " entities match this name.")
            if self.entity_scope is not None:
                print(f"When generating documentation for {self.entity_scope.full_canonical_path()}")
            print("The matching candidates are")
            for cand in candidates:
                fullname = cand.full_canonical_path() + ("(" + ",".join(param.typename for param in cand.params) + ")" if len(cand.params) > 0 else "")
                print(fullname)
            return None

        return candidates[0]
