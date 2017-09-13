from importer.entities import PageEntity, ClassEntity, GroupEntity, NamespaceEntity
from builder.entity_path import EntityPath
from doxydoc_plugin import DoxydocPlugin


class Plugin(DoxydocPlugin):
    def pages_list(self, builder, importer):
        entity = PageEntity()
        entity.kind = "special"
        entity.id = "plugins/list_specials/pages"
        entity.short_name = entity.name = "Tutorials"
        entity.innerpages = [e for e in importer.entities if e.kind == "page" and e.parent is None]
        entity.path = EntityPath()
        importer._add_docobj(entity)

        for page in entity.innerpages:
            page.parent = entity
        return builder.page_generator._page_with_entity("special_pages_list", entity, [entity])

    def classes_list(self, builder, importer):
        entity = GroupEntity()
        entity.kind = "special"
        entity.id = "plugins/list_specials/classes"
        entity.short_name = entity.name = "Classes"
        entity.inner_classes = [e for e in importer.entities if isinstance(e, ClassEntity) and e.parent_in_canonical_path() is None]
        entity.inner_namespaces = [e for e in importer.entities if isinstance(e, NamespaceEntity) and e.parent_in_canonical_path() is None]
        entity.path = EntityPath()
        importer._add_docobj(entity)

        return builder.page_generator._page_with_entity("special_class_list", entity, [entity])

    def group_list(self, builder, importer):
        entity = GroupEntity()
        entity.kind = "special"
        entity.id = "plugins/list_specials/groups"
        entity.short_name = entity.name = "Groups"
        entity.inner_groups = [e for e in importer.entities if isinstance(e, GroupEntity)]
        for e in entity.inner_groups:
            if e.parent is None:
                e.parent = entity

        entity.path = EntityPath()
        importer._add_docobj(entity)

        return builder.page_generator.group_page(entity)

    def define_pages(self, importer, builder):
        return [self.pages_list(builder, importer), self.classes_list(builder, importer), self.group_list(builder, importer)]
