from doxydoc_plugin import DoxydocPlugin


class Plugin(DoxydocPlugin):
    def __init__(self, config):
        if "items" not in config:
            print("navbar config did not contain an array of 'items' with page IDs")
            return

        self.config = config
        self.items = []

    def on_pre_build_html(self, importer, builder, entity2page):
        for pageID in self.config["items"]:
            entity = importer.get_entity(pageID)
            if entity is None:
                raise Exception("Could not add '{}' to the navbar because no entity with that ID could be found".format(pageID))

            try:
                page = entity2page[entity]
            except Exception as e:
                raise Exception("Could not add '{}' to the navbar because that entity is not part of any known page".format(pageID)) from e

            self.add(page)

    def add(self, page):
        self.items.append(page)
