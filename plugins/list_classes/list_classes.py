from importer.entities import PageEntity, ClassEntity, GroupEntity
from builder.entity_path import EntityPath


def define_page(importer, builder):
    entity = GroupEntity()
    entity.kind = "special"
    entity.id = "__plugin__list_classes"
    entity.short_name = entity.name = "Classes"
    entity.inner_classes = [e for e in importer.entities if isinstance(e, ClassEntity)]
    entity.path = EntityPath()

    return builder.page_generator.group_page(entity)
