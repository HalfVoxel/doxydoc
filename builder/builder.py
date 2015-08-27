import jinja2
from .writing_context import WritingContext
from .page import PageGenerator
from .entity_path import EntityPath


class Builder:
    def __init__(self, importer, settings):
        self.environment = None
        self.page_generator = PageGenerator(self)
        self.importer = importer
        self.settings = settings

        self.environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(settings.template_dir),
            line_statement_prefix="#", line_comment_prefix="##"
        )

        # Adds the field 'path' to all entities
        # This is used to look up on which
        # page that entity ends up
        # Might be a bit ugly to add fields
        # But it reduces a lot of clutter
        # This package assumes that all entities
        # have a path field
        for entity in importer.entities:
            entity.path = EntityPath()

    def add_filters(self, filters):

        def create_wrapper(key, fun, context):
            def wrapper(*args):
                return str(fun(context, *args))
            return wrapper

        for key, fun in filters.items():
            context = WritingContext(self.importer)
            wrapper = create_wrapper(key, fun, context)
            self.environment.filters[key] = wrapper

            wrapper_no_links = create_wrapper(key, fun, context.with_link_stripping())
            self.environment.filters[key + "_no_links"] = wrapper_no_links
