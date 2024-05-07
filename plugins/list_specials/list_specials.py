from typing import List
from importer.entities import PageEntity, ClassEntity, GroupEntity, NamespaceEntity, ExampleEntity
from builder.entity_path import EntityPath
from doxydoc_plugin import DoxydocPlugin
from importer.entities.page_entity import InnerPage


class Plugin(DoxydocPlugin):
    def pages_list(self, builder, importer, entities, additional_pages: List[PageEntity]):
        entity = PageEntity()
        entity.kind = "special"
        entity.id = "plugins/list_specials/pages"
        entity.short_name = entity.name = "Tutorials"
        entity.innerpages = [InnerPage(e, False) for e in entities if e.kind == "page" and e.parent is None]
        entity.innerpages += [InnerPage(p, False) for p in additional_pages]
        entity.path = EntityPath()
        importer._add_docobj(entity)

        for page in entity.child_entities():
            page.parent = entity
        return builder.page_generator._page_with_entity("special_pages_list", entity, [entity])

    def classes_list(self, builder, importer, entities):
        entity = GroupEntity()
        entity.kind = "special"
        entity.id = "plugins/list_specials/classes"
        entity.short_name = entity.name = "Classes"
        entity.inner_classes = [e for e in entities if isinstance(e, ClassEntity) and e.parent_in_canonical_path() is None]
        entity.inner_namespaces = [e for e in entities if isinstance(e, NamespaceEntity) and e.parent_in_canonical_path() is None]
        entity.path = EntityPath()
        importer._add_docobj(entity)

        return builder.page_generator._page_with_entity("special_class_list", entity, [entity])

    def group_list(self, builder, importer, entities):
        entity = GroupEntity()
        entity.kind = "special"
        entity.id = "plugins/list_specials/groups"
        entity.short_name = entity.name = "Groups"
        entity.inner_groups = [e for e in entities if isinstance(e, GroupEntity)]
        for e in entity.inner_groups:
            if e.parent is None:
                e.parent = entity

        entity.path = EntityPath()

        if len(entity.inner_groups) > 0:
            importer._add_docobj(entity)
            return builder.page_generator.group_page(entity)

    def examples_list(self, builder, importer, entities):
        return
    
        entity = GroupEntity()
        entity.kind = "special"
        entity.id = "plugins/list_specials/examples"
        entity.short_name = entity.name = "Examples"
        entity.inner_groups = [e for e in entities if isinstance(e, ExampleEntity)]
        entity.path = EntityPath()

        if len(entity.inner_groups) > 0:
            importer._add_docobj(entity)
            return builder.page_generator.group_page(entity)

    def define_pages(self, importer, builder):
        original_entities = importer.entities[:]
        examples = self.examples_list(builder, importer, original_entities)
        groups = self.group_list(builder, importer, original_entities)
        classes = self.classes_list(builder, importer, original_entities)
        pages = self.pages_list(builder, importer, original_entities, [p.primary_entity for p in [examples, groups, classes] if p is not None])
        return [p for p in [pages, classes, groups, examples] if p is not None]
