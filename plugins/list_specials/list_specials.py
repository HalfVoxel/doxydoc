from importer.entities import PageEntity, ClassEntity, GroupEntity, NamespaceEntity
from builder.entity_path import EntityPath


def pages_list(builder, importer):
    entity = PageEntity()
    entity.kind = "special"
    entity.id = "__plugin__list_specials"
    entity.short_name = entity.name = "Tutorials"
    entity.subpages = [e for e in importer.entities if e.kind == "page" and e.parent is None]
    entity.path = EntityPath()
    for page in entity.subpages:
        page.parent = entity
    return builder.page_generator._page_with_entity("special_pages_list", entity, [entity])


def classes_list(builder, importer):
    entity = GroupEntity()
    entity.kind = "special"
    entity.id = "__plugin__list_classes"
    entity.short_name = entity.name = "Classes"
    entity.inner_classes = [e for e in importer.entities if isinstance(e, ClassEntity) and e.parent_in_canonical_path() is None]
    entity.inner_namespaces = [e for e in importer.entities if isinstance(e, NamespaceEntity) and e.parent_in_canonical_path() is None]
    entity.path = EntityPath()

    #return builder.page_generator.group_page(entity)
    return builder.page_generator._page_with_entity("special_class_list", entity, [entity])


def group_list(builder, importer):
    entity = GroupEntity()
    entity.kind = "special"
    entity.id = "__plugin__list_groups"
    entity.short_name = entity.name = "Groups"
    entity.inner_groups = [e for e in importer.entities if isinstance(e, GroupEntity)]
    for e in entity.inner_groups:
        if e.parent is None:
            e.parent = entity

    entity.path = EntityPath()

    return builder.page_generator.group_page(entity)


def define_pages(importer, builder):
    return [pages_list(builder, importer), classes_list(builder, importer), group_list(builder, importer)]
