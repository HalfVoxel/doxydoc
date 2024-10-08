import os
from builder.builder import Builder
from doxydoc_plugin import DoxydocPlugin
from importer.entities.entity import Entity
from importer.importer_context import ImporterContext
import xml.etree.ElementTree as ET

class Plugin(DoxydocPlugin):
    image_directory: str | None

    def __init__(self, config):
        super().__init__(config)
        self.image_directory = config["image_directory"] if config is not None else None

    def on_pre_build_html(self, importer, builder: Builder, entity2page):
        if self.image_directory is None:
            print("No image directory specified for inspector screenshots. Skipping.")
            return

        ctx: ImporterContext = importer.ctx
        entities: list[Entity] = importer.entities
        print("Checking for inspector screenshots")
        used = set()
        image_names = os.listdir(os.path.join(builder.settings.out_dir, self.image_directory))
        # Filter out non-png files and scaled images (e.g. @2x)
        image_names = set(im for im in image_names if im.endswith(".png") and "@" not in im)
        for entity in entities:
            if entity.kind != "class":
                continue

            filename = entity.name + ".png"
            if filename in image_names:
                localPath = self.image_directory + "/" + filename
                used.add(filename)
                p = ET.Element("para")
                p.insert(0, ET.Element("image", { "src": localPath, "alt": 'Inspector Screenshot' }))
                entity.detaileddescription.insert(0, p)
        
        unused = image_names - used
        if len(unused) > 0:
            print("Unused inspector screenshots:")
            for f in unused:
                print("  " + f)
            print("")
