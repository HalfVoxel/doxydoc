import os
from builder.builder import Builder
from doxydoc_plugin import DoxydocPlugin
from importer.entities.entity import Entity
from importer.importer_context import ImporterContext
import xml.etree.ElementTree as ET

class Plugin(DoxydocPlugin):
    def __init__(self, config):
        super().__init__(config)

    def on_pre_build_html(self, importer, builder: Builder, entity2page):
        ctx: ImporterContext = importer.ctx
        entities: list[Entity] = importer.entities
        print("Checking for inspector screenshots")
        used = set()
        ROOT_DIR = "images/generated/inspectors"
        for entity in entities:
            if entity.kind != "class":
                continue

            filename = entity.name + ".png"
            localPath = ROOT_DIR + "/" + filename
            full_path = os.path.join(builder.settings.out_dir, localPath)
            if os.path.isfile(full_path):
                used.add(filename)
                p = ET.Element("para")
                p.insert(0, ET.Element("image", { "src": localPath, "alt": 'Inspector Screenshot' }))
                entity.detaileddescription.insert(0, p)
        
        unused = set(os.listdir(os.path.join(builder.settings.out_dir, ROOT_DIR))) - used
        if len(unused) > 0:
            print("Unused inspector screenshots:")
            for f in unused:
                print("  " + f)
            print("")
