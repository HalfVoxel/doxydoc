class DoxydocPlugin:
    def __init__(self, config):
       self.config = config

    def define_pages(self, importer, builder):
        return []

    def on_pre_build_html(self, importer, builder, entity2page):
        pass

    def on_post_build_html(self, importer, builder, entity2page):
        pass
