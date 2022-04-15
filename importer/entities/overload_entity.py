from importer.entities.member_entity import MemberEntity
from .entity import Entity
from .class_entity import ClassEntity
from importer.importer_context import ImporterContext
from typing import Any, Dict, List, Optional, Set, Tuple
import itertools
import functools


class OverloadEntity(Entity):
    def __init__(self) -> None:
        super().__init__()
        self.inner_members: List[MemberEntity] = []
        self.parent: Optional[Entity] = None
        self.virtual: Optional[str] = None
        self.static: bool = False
        self.override: Optional[str] = None
        self.abstract: bool = False
        self.defined_in_entity: Optional[ClassEntity] = None
        self.protection: Optional[str] = None
        self.argsstring: Optional[str] = None
    
    def calculate_optimized_params(self):
        '''
        Calculates an argument string that encompases all the overloads.
        For example
        ```
        void f(a, b)
        void f(a, b, c)
        ```
        will be combined into the argument string "a, b, [c]" where the brackets indicate that c is optional.
        '''
        variants = set()
        param_names = set()
        avg_index = dict()
        variant_sets = []
        for member in self.inner_members:
            assert member.hasparams
            param_alts = []
            for i, param in enumerate(member.params):
                alts = []
                if param.default_value is not None:
                    alts.append(None)
                
                alts.append(param.name)
                param_alts.append(alts)
                param_names.add(param.name)
                avg_index.setdefault(param.name, []).append(i)
            
            variant_set = []
            for alt in itertools.product(*param_alts):
                names = [x for x in alt if x is not None]
                variants.add(tuple(names))
                variant_set.append(tuple(names))
            variant_sets.append(set(variant_set))
        
        avg_index = { k: sum(v)/len(v) for k, v in avg_index.items() }
        
        inconsistent: Set[str] = set()
        # (a, b) = 1 means a > b, -1 means a < b
        ordering: Dict[Tuple[str,str], int] = dict()
        optional: Set[str] = set()
        required: Set[str] = set()
        for name in param_names:
            before: Set[str] = set()
            after: Set[str] = set()
            is_required = True
            for variant in variants:
                ls = list(variant)
                if name not in ls:
                    is_required = False
                    continue

                index = ls.index(name)
                for x in ls[:index]:
                    ordering[(name, x)] = 1
                    before.add(x)
                for x in ls[index+1:]:
                    ordering[(name, x)] = -1
                    after.add(x)
            
            if is_required:
                required.add(name)

            if len(before.intersection(after)) > 0:
                # Inconsistent ordering
                inconsistent.add(name)
        
        def compare_order(a: str, b: str):
            if (a,b) in ordering:
                return ordering[(a,b)]
            else:
                # Unordered
                return avg_index[a] - avg_index[b]
        
        def contains_sublist(ls: List[Any], sublist: List[Any]) -> bool:
            res = False
            for idx in range(len(ls) - len(sublist) + 1):
                if ls[idx:idx + len(sublist)] == sublist:
                    res = True 
                    break
            
            return res

        sorted_param_names = sorted(param_names, key=functools.cmp_to_key(compare_order))

        for k in range(1, len(sorted_param_names)):
            for i in reversed(range(len(sorted_param_names) - k + 1)):
                group = sorted_param_names[i:i+k]
                is_valid_optional_group = True
                if len(group) != k or any(isinstance(name, list) for name in group):
                    continue
                
                for variant in variants:
                    can_remove = contains_sublist(list(variant), group)
                    if can_remove:
                        # Try removing
                        ls = list(variant)
                        for x in group:
                            ls.remove(x)
                        can_remove &= tuple(ls) in variants
                    can_append = set(variant).isdisjoint(group)
                    if can_append:
                        # Try inserting the group somewhere
                        ls = list(variant)
                        any_append = False
                        for insert_index in range(len(ls)+1):
                            ls2 = ls[:insert_index] + group + ls[insert_index:]
                            any_append |= tuple(ls2) in variants
                        
                        can_append &= any_append
                    if not (can_remove or can_append):
                        is_valid_optional_group = False
                
                if is_valid_optional_group:
                    sorted_param_names = sorted_param_names[:i] + [group] + sorted_param_names[i+k:]
        
        def compress(ls: List[str]) -> List[str]:
            out = []
            i = 0
            while i < len(ls):
                out.append(ls[i])
                while i+1 < len(ls) and ls[i] == "..." and ls[i+1] == "...":
                    i += 1
                
                i += 1
            
            return out

        for i in range(len(sorted_param_names)):
            if isinstance(sorted_param_names[i], list):
                for j in range(len(sorted_param_names[i])):
                    if sorted_param_names[i][j] in inconsistent:
                        sorted_param_names[i][j] = "..."
                
                compress(sorted_param_names[i])
            else:
                name = sorted_param_names[i]
                if (name in inconsistent) or (name not in required):
                    sorted_param_names[i] = "..."
        sorted_param_names = compress(sorted_param_names)

        # If the last item is ... and we can remove the ... to make a valid variant
        # then the last item should be optional.
        if len(sorted_param_names) > 0 and sorted_param_names[-1] == "..." and all(isinstance(x, str) for x in sorted_param_names[:-1]) and tuple(sorted_param_names[:-1]) in variants:
            sorted_param_names[-1] = ["..."]
        
        argsstring = []
        for names in sorted_param_names:
            if isinstance(names, list):
                argsstring.append("[" + ", ".join(names) + "]")
            else:
                argsstring.append(names)
        self.argsstring = ", ".join(argsstring)
            
    def child_entities(self):
        return self.inner_members

    def parent_in_canonical_path(self) -> Entity:
        return self.parent

    def read_from_xml(self, ctx: ImporterContext) -> None:
        raise Exception("This entity type does not have an XML representation")
