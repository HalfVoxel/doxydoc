import os


class Page:
    def __init__(self, title, path, template, primary_entity, entities):
        self.title = title
        self.path = path
        self.template = template
        self.primary_entity = primary_entity
        self.entities = entities


class PageGenerator:

    def __init__(self):
        self.reserved_filenames = set()

    def reserve_filename(self, filename):
        self.reserved_filenames.update(filename)

    def generate_filename(self, name, extension):
        filename = name.lower().replace(" ", "_").replace(".", "_")
        # Strip non alphanumeric characters
        filename = "".join([c for c in filename if c.isalnum() or c == "_"])

        if len(filename) > 40:
            filename = filename[0:41]

        name_with_extension = filename + "." + extension
        if name_with_extension not in self.reserved_filenames:
            self.reserve_filename(name_with_extension)
            return name_with_extension

        for i in range(1, 100):
            name_with_extension = filename + i + "." + extension
            if name_with_extension not in self.reserved_filenames:
                self.reserve_filename(name_with_extension)
                return name_with_extension

        raise "Cannot find a valid filename. Last try was " + name_with_extension

    def _page(self, template, entity, entities):
        page = Page(entity.name,
                    self.generate_filename(entity.name, "html"),
                    template,
                    entity,
                    entities)

        assert entity in entities

        for entity in page.entities:
            if entity.path.path is not None:
                print ("Warning: Entity included in multiple pages: " + entity.id)

            entity.path.path = page.path

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

    def generate(self, page, state):
        f = open(os.path.join(state.settings.outdir, page.path), "w")
        template = state.environment.get_template(page.template + ".html")
        print("Rendering entity " + page.primary_entity.name)
        text = template.render(entity=page.primary_entity, state=state)
        f.write(text)
        f.close()
