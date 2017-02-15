from importer.entities import PageEntity
from builder.entity_path import EntityPath


def define_page(importer, builder):
    entity = PageEntity()
    entity.kind = "special"
    entity.id = "__plugin__list_specials"
    entity.short_name = entity.name = "Related Pages"
    entity.subpages = [e for e in importer.entities if e.kind == "page"]
    entity.path = EntityPath()
    page = builder.page_generator._page_with_entity("special_pages_list", entity, [entity])
    return page
