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
        ctx.relpath = self.relpath
        return ctx

    def getref(self, xml) -> Entity:
        return self.state.ctx.getref(xml)

    def getref_from_name(self, name: str):
        name = name.strip()
        name = name.replace("::",".")
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
        if paramPart != "":
            candidateParamNames = [",".join(param.typename for param in cand.params) for cand in candidates]
            candidates = [c for c, paramNames in zip(candidates, candidateParamNames) if paramNames == paramPart]

        if len(candidates) == 0:
            print()
            print("Could not find any entity with the name '" + name + "'.")
            if len(pathCandidates) > 0:
                print("There were some entities that matched the name but not the parameter list. The candidates are:")
                for cand in pathCandidates:
                    fullname = cand.full_canonical_path() + ("(" + ",".join(param.typename for param in cand.params) + ")" if len(cand.params) > 0 else "")
                    print(fullname)
            return None

        elif len(candidates) > 1:
            print()
            print("Ambigious reference '" + name + "' in a tag. " + str((len(candidates))) + " entities match this name.")
            print("The matching candidates are")
            for cand in candidates:
                fullname = cand.full_canonical_path() + ("(" + ",".join(param.typename for param in cand.params) + ")" if len(cand.params) > 0 else "")
                print(fullname)
            return None

        return candidates[0]
