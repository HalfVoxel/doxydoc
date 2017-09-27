import os
from . import layout_helpers
from typing import List, Set, cast, TYPE_CHECKING
from importer.entities import Entity, ClassEntity, FileEntity, NamespaceEntity, ExampleEntity, PageEntity, GroupEntity
from .writing_context import WritingContext
if TYPE_CHECKING:
    from .builder import Builder


class Page:
    def __init__(self, path: str, template: str, primary_entity: Entity, entities: List[Entity]) -> None:
        self.title = "Untitled"
        self.path = path
        self.template = template
        self.primary_entity = primary_entity
        self.entities = entities


def generate_io_safe_name(filename: str, tail: str, reserved: Set[str]) -> str:
        # filename_comps = name.split(":")

        # Strip non alphanumeric characters
        # filename_comps = [
        #    "".join([c for c in filename if c.isalnum() or c == "_"])
        #    for filename in filename_comps]

        # filename = "/".join(filename_comps)

        if len(filename) > 40:
            filename = filename[0:41]

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
            return entity.name

    def entity_path(self, entity: Entity) -> str:
        ''' Desired path for an entity in the file system. Does not include the file extension. May change due to conflicts. '''
        path = []
        ent = entity
        while ent is not None:
            path.append(ent)
            ent = ent.parent_in_canonical_path()

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

        used_anchors = set()  # type: Set[str]
        for entity in page.entities:
            if entity.path.path is not None:
                print("Warning: Entity included in multiple pages: " + entity.id)

            entity.path.path = page.path
            if entity is not primary_entity:
                # Set anchor
                entity.path.anchor = generate_io_safe_name(entity.name, "", used_anchors)
                used_anchors.add(entity.path.anchor)

        return page

    def _page_with_entity(self, template: str, primary_entity: Entity, entities: List[Entity]) -> Page:
        desired_path = self.entity_path(primary_entity)
        page = self._page(template, desired_path, primary_entity, entities)
        page.title = primary_entity.name
        return page

    def class_page(self, entity: ClassEntity) -> Page:
        inner_entities = [cast(Entity, entity)] + entity.sections + entity.members
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

        text = template.render(
            page=page,
            entity=page.primary_entity,
            state=self.builder.importer,
            settings=self.builder.settings,
            layout=layout_helpers,
            relpath=relpath,
            in_tree=in_tree,
            sorted=sort_entities,
            plugins=self.builder.plugin_context,
        )
        f.write(text)
        f.close()
