import os
from typing import cast
from builder.builder import Builder
from doxydoc_plugin import DoxydocPlugin
from importer.entities.class_entity import ClassEntity
from importer.entities.entity import Entity
from importer.importer_context import ImporterContext

class Plugin(DoxydocPlugin):
    output_path: str | None

    def __init__(self, config):
        super().__init__(config)
        self.output_path = config["output_path"] if config is not None else None


    def on_post_build_html(self, importer: ImporterContext, builder: Builder, entity2page):
        if self.output_path is None:
            print("No output path specified for url export. Skipping.")
            return
        entities = cast(list[Entity], importer.entities)
        output = []
        path_mapping = {}
        for entity in entities:
            if isinstance(entity, ClassEntity):
                inherit_path = []
                e = entity
                while e is not None:
                    ext = e.inherits_from[0] if e.inherits_from else None
                    if ext is not None:
                        inherit_path.append(ext.name)
                        e = ext.entity
                    else:
                        break

                path_mapping[entity.full_canonical_path(".")] = entity.path.full_url() + "\t" + ".".join(reversed(inherit_path))
        
        output = [f"{k}\t{v}" for (k,v) in path_mapping.items()]
        output.sort()
        with open(os.path.join(builder.settings.out_dir, self.output_path), "w") as f:
            f.write("\n".join(output))
