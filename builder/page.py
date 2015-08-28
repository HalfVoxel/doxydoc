import os
from . import layout_helpers


class Page:
    def __init__(self, title, path, template, primary_entity, entities):
        self.title = title
        self.path = path
        self.template = template
        self.primary_entity = primary_entity
        self.entities = entities


def generate_io_safe_name(name, tail, reserved):
        filename = name.lower().replace(" ", "_").replace(".", "_")
        # Strip non alphanumeric characters
        filename = "".join([c for c in filename if c.isalnum() or c == "_"])

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


class PageGenerator:

    def __init__(self, builder):
        self.builder = builder
        self.reserved_filenames = set()

    def reserve_filename(self, filename):
        self.reserved_filenames.add(filename)

    def _page(self, template, primary_entity, entities):
        path = generate_io_safe_name(primary_entity.name, ".html", self.reserved_filenames)
        self.reserve_filename(path)

        page = Page(primary_entity.name,
                    path,
                    template,
                    primary_entity,
                    entities)

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

    def class_page(self, entity):
        page = self._page("classdoc", entity, [entity] + entity.sections + entity.members)
        return page

    def page_page(self, entity):
        page = self._page("pagedoc", entity, [entity] + entity.sections)
        return page

    def file_page(self, entity):
        page = self._page("filedoc", entity, [entity] + entity.sections)
        return page

    def example_page(self, entity):
        page = self._page("exampledoc", entity, [entity] + entity.sections)
        return page

    def generate(self, page):
        f = open(os.path.join(self.builder.settings.out_dir, page.path), "w")
        template = self.builder.environment.get_template(page.template + ".html")
        text = template.render(
            entity=page.primary_entity,
            state=self.builder.importer,
            layout=layout_helpers
        )
        f.write(text)
        f.close()
