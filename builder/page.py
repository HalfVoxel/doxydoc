import os
from . import layout_helpers


class Page:
    def __init__(self, path, template, primary_entity, entities):
        self.title = "Untitled"
        self.path = path
        self.template = template
        self.primary_entity = primary_entity
        self.entities = entities


def generate_io_safe_name(filename, tail, reserved):
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

        raise "Cannot find a valid filename. Last try was " + name_with_tail


def clean_io_name(name):
    name = name.lower().replace(" ", "_").replace(".", "").replace(":", "").replace("/", "")

    # Replace non-alphanumeric characters with underscores
    name = "".join([c for c in name if c.isalnum() or c == "_"])

    # Make sure the name is not empty
    if len(name) == 0:
        name = "_"

    return name


class PageGenerator:

    def __init__(self, builder, default_writing_context):
        self.builder = builder
        self.reserved_filenames = set()
        self.default_writing_context = default_writing_context

    def reserve_filename(self, filename):
        self.reserved_filenames.add(filename)

    def entity_path(self, entity):
        if hasattr(entity, "parent_in_canonical_path"):
            path = []
            ent = entity
            while ent is not None:
                path.append(ent)
                ent = ent.parent_in_canonical_path()

            path.reverse()

            # Join components either with underscores or with slashes
            separator = '_' if self.builder.settings.flat_file_hierarchy else '/'

            return separator.join([clean_io_name(component.name) for component in path])
        else:
            return clean_io_name(entity.short_name)

    def _page(self, template, desired_path, primary_entity, entities):
        path = generate_io_safe_name(desired_path, ".html", self.reserved_filenames)
        self.reserve_filename(path)

        page = Page(path,
                    template,
                    primary_entity,
                    entities)

        if primary_entity is not None:
            assert primary_entity in entities

        used_anchors = set()
        for entity in page.entities:
            if entity.path.path is not None:
                print ("Warning: Entity included in multiple pages: " + entity.id)

            entity.path.path = page.path
            if entity is not primary_entity:
                # Set anchor
                entity.path.anchor = generate_io_safe_name(entity.name, "", used_anchors)
                used_anchors.add(entity.path.anchor)

        return page

    def _page_with_entity(self, template, primary_entity, entities):
        desired_path = self.entity_path(primary_entity)
        page = self._page(template, desired_path, primary_entity, entities)
        page.title = primary_entity.name
        return page

    def class_page(self, entity):
        inner_entities = [entity] + entity.sections + entity.members
        page = self._page_with_entity("class", entity, inner_entities)
        return page

    def page_page(self, entity):
        page = self._page_with_entity("page", entity, [entity] + entity.sections)
        return page

    def file_page(self, entity):
        page = self._page_with_entity("file", entity, [entity] + entity.sections)
        return page

    def example_page(self, entity):
        page = self._page_with_entity("example", entity, [entity] + entity.sections)
        return page

    def namespace_page(self, entity):
        page = self._page_with_entity("namespace", entity, [entity] + entity.sections)
        return page

    def generate(self, page):
        path = os.path.join(self.builder.settings.out_dir, page.path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        f = open(path, "w")
        template = self.builder.environment.get_template(page.template + ".html")

        dir_in_outdir = os.path.dirname(page.path)

        # Relative paths from this page to target
        def relpath(target):
            # Absolute path
            if target.startswith("http://") or target.startswith("https://"):
                return target
            return os.path.relpath(target, dir_in_outdir)

        self.default_writing_context.relpath = relpath

        text = template.render(
            page=page,
            entity=page.primary_entity,
            state=self.builder.importer,
            layout=layout_helpers,
            relpath=relpath,
            plugins=self.builder.plugin_context
        )
        f.write(text)
        f.close()
