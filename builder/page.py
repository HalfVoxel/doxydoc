from builder.str_tree import StrTree
from importer.entities.member_entity import MemberEntity
from importer.entities.overload_entity import OverloadEntity
import os
from . import layout_helpers
from typing import Any, Callable, List, Optional, Set, cast, TYPE_CHECKING
from importer.entities import Entity, ClassEntity, FileEntity, NamespaceEntity, ExampleEntity, PageEntity, GroupEntity
from .writing_context import WritingContext
import itertools
from builder.entity_path import EntityPath
import builder.layout
import xml.etree.ElementTree as ET

if TYPE_CHECKING:
    from .builder import Builder


class Page:
    def __init__(self, path: str, template: str, primary_entity: Entity, entities: List[Entity]) -> None:
        self.title = "Untitled"
        self.path = path
        self.template = template
        self.primary_entity = primary_entity
        self.entities = entities

        self.used_anchors = set()  # type: Map[Entity,str]
        self.anchors = dict()
        for entity in entities:
            if entity.path.path is not None:
                print("Warning: Entity included in multiple pages: " + entity.id)

            entity.path.path = path
            if entity is not primary_entity:
                # Set anchor
                entity.path.anchor = generate_io_safe_name(entity.name, "", self.used_anchors)
                self.used_anchors.add(entity.path.anchor)
                self.anchors[entity] = entity.path.anchor

    def get_local_anchor(self, entity: Entity) -> str:
        if entity in self.anchors:
            return self.anchors[entity]
        else:
            anchor = generate_io_safe_name(entity.name, "", self.used_anchors)
            self.used_anchors.add(anchor)
            self.anchors[entity] = anchor
            return anchor


def generate_io_safe_name(filename: str, tail: str, reserved: Set[str]) -> str:
        # filename_comps = name.split(":")

        # Strip non alphanumeric characters
        # filename_comps = [
        #    "".join([c for c in filename if c.isalnum() or c == "_"])
        #    for filename in filename_comps]

        # filename = "/".join(filename_comps)

        if len(filename) > 40:
            filename = filename[0:41]

        # Make sure the name only contains alphanumeric characters, underscores and hyphens
        # This is required to make sure it is a valid anchor for example
        # See https://stackoverflow.com/questions/1391802/can-a-dom-element-have-an-id-that-contains-a-space
        filename = "".join([c for c in filename if c.isalnum() or c == "_" or c == "-" or c == "/"])

        name_with_tail = filename + tail

        if name_with_tail not in reserved:
            return name_with_tail

        for i in range(2, 100):
            name_with_tail = filename + str(i) + tail
            if name_with_tail not in reserved:
                return name_with_tail

        raise Exception("Cannot find a valid filename. Last try was " + name_with_tail)


def clean_io_name(name: str) -> str:
    name = name.lower().replace(" ", "_").replace(".", "").replace(":", "").replace("/", "")

    # Replace non-alphanumeric characters with underscores
    name = "".join([c for c in name if c.isalnum() or c == "_"])

    # Make sure the name is not empty
    if len(name) == 0:
        name = "_"

    return name


class PageGenerator:

    def __init__(self, builder: 'Builder', default_writing_context: WritingContext) -> None:
        self.builder = builder
        self.reserved_filenames = set()  # type: Set[str]
        self.default_writing_context = default_writing_context

    def reserve_filename(self, filename: str) -> None:
        self.reserved_filenames.add(filename)

    def entity_path_name(self, entity: Entity) -> str:
        ''' Name an entity uses in the file system '''
        if entity.id == "indexpage":
            return "index"
        else:
            return entity.short_name

    def entity_path(self, entity: Entity) -> str:
        ''' Desired path for an entity in the file system. Does not include the file extension. May change due to conflicts. '''
        path = []
        ent = entity
        counter = 0
        while ent is not None:
            if ent == entity or ent.include_in_filepath:
                path.append(ent)
            ent = ent.parent_in_canonical_path()
            counter += 1
            if counter > 50:
                raise Exception(f"Probable infinite loop in canonical path: {path}")

        path.reverse()

        # Join components either with underscores or with slashes
        separator = '_' if self.builder.settings.flat_file_hierarchy else '/'

        return separator.join([clean_io_name(self.entity_path_name(component)) for component in path])

    def _page(self, template: str, desired_path: str, primary_entity: Entity, entities: List[Entity]) -> Page:
        path = generate_io_safe_name(desired_path, ".html", self.reserved_filenames)
        self.reserve_filename(path)

        page = Page(path,
                    template,
                    primary_entity,
                    entities)

        if primary_entity is not None:
            assert primary_entity in entities

        return page

    def _page_with_entity(self, template: str, primary_entity: Entity, entities: List[Entity]) -> Page:
        desired_path = self.entity_path(primary_entity)
        page = self._page(template, desired_path, primary_entity, entities)
        page.title = primary_entity.name
        return page

    def class_page(self, entity: ClassEntity) -> Page:
        inner_entities = [cast(Entity, entity)] + entity.sections + entity.members
        sub_entities = []
        for e in inner_entities:
            if isinstance(e, MemberEntity) and e.kind == "enum":
                sub_entities += e.members

        inner_entities += sub_entities
        if self.builder.settings.separate_function_pages:
            # These functions will go into separate pages
            inner_entities = [e for e in inner_entities if e.kind != "function"]

        page = self._page_with_entity("class", entity, inner_entities)
        return page

    def page_page(self, entity: PageEntity) -> Page:
        page = self._page_with_entity("page", entity, [cast(Entity, entity)] + entity.sections)
        return page

    def file_page(self, entity: FileEntity) -> Page:
        page = self._page_with_entity("file", entity, [cast(Entity, entity)] + entity.sections)
        return page

    def group_page(self, entity: GroupEntity) -> Page:
        page = self._page_with_entity("group", entity, [cast(Entity, entity)] + entity.sections)
        return page

    def example_page(self, entity: ExampleEntity) -> Page:
        page = self._page_with_entity("example", entity, [cast(Entity, entity)] + entity.sections)
        return page

    def namespace_page(self, entity: NamespaceEntity) -> Page:
        inner_entities = [cast(Entity, entity)] + entity.sections + entity.members
        page = self._page_with_entity("namespace", entity, inner_entities)
        return page

    def function_overload_pages(self, class_entity: ClassEntity) -> List[Page]:
        def combine_description(ctx: WritingContext, entities: List[MemberEntity]):
            descriptions: Set[str] = set()
            for e in entities:
                buffer = StrTree(ignore_html=True)
                builder.layout.description(ctx, e.briefdescription, buffer)
                descriptions.add(str(buffer).strip())

            if len(descriptions) == 1:
                return entities[0].briefdescription
            else:
                longest_prefix = descriptions.pop()
                original_prefix = longest_prefix
                while len(descriptions) > 0:
                    s = descriptions.pop()
                    max_index = 0
                    while max_index < min(len(s), len(longest_prefix)):
                        if s[max_index] != longest_prefix[max_index]:
                            break
                        max_index += 1

                    longest_prefix = longest_prefix[:max_index]

                longest_prefix = longest_prefix.strip()
                while len(longest_prefix) > 0 and longest_prefix[-1] in "(<,":
                    longest_prefix = longest_prefix[:-1]

                if len(longest_prefix) < 3:
                    longest_prefix = ""

                if original_prefix != longest_prefix:
                    longest_prefix += "..."

                desc = ET.Element("briefdescription")
                para = ET.Element("para")
                para.text = longest_prefix
                desc.append(para)
                return desc

        def combine_detailed_desription(entities: List[MemberEntity]) -> Optional[ET.Element]:
            # Try to find an image which is shared among all overloads.
            # This can be used as a representative image to display on the overload page.
            shared_images = None
            for e in entities:
                s = set([im.attrib["name"] for im in e.detaileddescription.findall(".//image")])
                if shared_images is None:
                    shared_images = s
                else:
                    shared_images = s.intersection(shared_images)

            if shared_images is not None and len(shared_images) > 0:
                desc = ET.Element("detaileddescription")
                para = ET.Element("para")
                img = ET.Element("image")
                img.attrib["name"] = list(shared_images)[0]
                para.append(img)
                desc.append(para)
                return desc
            else:
                return None

        result = []
        for ((kind, name), overloads) in itertools.groupby(class_entity.all_members, key=lambda e: (e.kind, e.name)):
            if kind == "function":
                overloads = list(overloads)
                entity = OverloadEntity(name, class_entity, overloads)
                entity.briefdescription = combine_description(self.default_writing_context.with_link_stripping(), overloads)
                entity.detaileddescription = combine_detailed_desription(overloads)
                entity.path = EntityPath()
                self.builder.importer._add_docobj(entity)

                result.append(self._page_with_entity("function_overloads", entity, [entity] + overloads))
        return result

    def generate(self, page: Page) -> None:
        path = os.path.join(self.builder.settings.out_dir, page.path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        f = open(path, "w")
        template = self.builder.environment.get_template(page.template + ".html")

        dir_in_outdir = os.path.dirname(page.path)

        # Relative paths from this page to target
        def relpath(target: str) -> str:
            # Absolute path
            if target.startswith("http://") or target.startswith("https://"):
                return target

            return os.path.relpath(target, dir_in_outdir)

        def in_tree(other: Entity) -> bool:
            ent = page.primary_entity
            while ent is not None:
                if ent == other:
                    return True
                ent = ent.parent_in_canonical_path()

        def sort_entities(list: List[Entity]) -> List[Entity]:
            return sorted(list, key=lambda e: e.sorting_order)

        self.default_writing_context.relpath = relpath
        self.default_writing_context.page = page
        self.default_writing_context.entity_scope = page.primary_entity
        self.default_writing_context.sort_entities = sort_entities

        text = template.render(
            page=page,
            entity=page.primary_entity,
            state=self.builder.importer,
            layout=layout_helpers,
            relpath=relpath,
            in_tree=in_tree,
            sorted=sort_entities,
            settings=self.builder.settings,
            plugins=self.builder.plugin_context,
        )
        f.write(text)
        f.close()

        if self.builder.settings.doxygen_redirects and page.primary_entity.filename is not None:
            fname = os.path.splitext(os.path.basename(page.primary_entity.filename))[0] + self.builder.settings.doxygen_redirect_extension
            path = os.path.join(self.builder.settings.out_dir, fname)
            f = open(path, "w")
            f.write(text)
            f.close()

