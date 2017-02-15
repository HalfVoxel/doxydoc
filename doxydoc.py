# from doxybase import *
from os import listdir
from os.path import isfile, isdir, join
from progressbar import progressbar
from importer import Importer
from importer.entities import ExternalEntity, Entity
import shutil
import os
import builder.layout
from builder import Builder
import builder.settings
from subprocess import call
from typing import Any, List
# import doxyspecial
import argparse
import plugins.list_specials.list_specials
import plugins.navbar.navbar


class DoxyDoc:

    def __init__(self) -> None:
        self.importer = Importer()
        self.settings = builder.settings.Settings()
        self.settings.out_dir = "html"
        self.settings.template_dirs = ["templates"]
        self.plugin_context = {}  # type: Dict[str,Any]

    def load_plugins(self) -> None:

        if not self.settings.args.quiet:
            print("Loading Plugins...")

        dirs = ["plugins", "themes"]

        for dir in dirs:
            plugins = [f for f in listdir(dir) if isdir(join(dir, f))]

            for plugin in plugins:
                self.settings.template_dirs.append(join(dir, plugin, "templates"))

        print(self.settings.template_dirs)

    def read_external(self) -> None:
        if not self.settings.args.quiet:
            print("Reading exteral...")

        try:
            f = open("external.csv")
        except:
            print("Could not read external.csv")

        for line in f:
            arr = line.split(",")
            if len(arr) >= 2:
                name = arr[0].strip()
                url = arr[1].strip()
                obj = ExternalEntity(url)
                obj.id = "__external__" + name
                obj.kind = "external"
                obj.name = name
                self.importer._add_docobj(obj)

        f.close()

    def copy_resources_dir(self, source_dir: str, target_dir: str) -> None:
        try:
            for root, dirs, files in os.walk(source_dir):
                dstroot = root.replace(source_dir + "/", "").replace(source_dir, "")

                target_dir = os.path.join(target_dir, dstroot)
                try:
                    os.makedirs(target_dir)
                except:
                    pass

                for fn in files:
                    source_path = os.path.join(root, fn)
                    target_path = os.path.join(target_dir, fn)

                    if source_path.endswith(".scss"):
                        target_path = target_path.replace(".scss", ".css")
                        # Process scss files using sass
                        call(["sass", os.path.realpath(source_path), os.path.realpath(target_path)])
                    else:
                        shutil.copy2(source_path, target_path)

                # Copy subdirectories
                for subdir in dirs:
                    source_subdir = os.path.join(source_dir, subdir)
                    target_subdir = os.path.join(target_dir, subdir)
                    self.copy_resources_dir(source_subdir, target_subdir)
        except OSError as e:
            print("Error while copying resources: " + str(e))

    def copy_resources(self) -> None:
        if not self.settings.args.quiet:
            print("Copying resources...")

        target_dir = os.path.join(self.settings.out_dir, "resources")

        self.copy_resources_dir("resources", target_dir)

        themes = [f for f in listdir("themes") if isdir(join("themes", f))]
        for moduleName in themes:
            resbase = os.path.join(os.path.join("themes", moduleName), "resources")
            self.copy_resources_dir(resbase, target_dir)

        target_dir = os.path.join(self.settings.out_dir, "images")
        self.copy_resources_dir("input/images", target_dir)

    def read_prefs(self) -> None:
        if not self.settings.args.quiet:
            print("Reading resources...")

    def find_xml_files(self, path: str) -> List[str]:
        return [join(path, f) for f in listdir(path)
                if isfile(join(path, f)) and f.endswith(".xml")]

    def scan_input(self) -> None:
        if not self.settings.args.quiet:
            print("Scanning input")

        self.importer.read(self.find_xml_files("input/xml"))

    def create_navbar(self, pages: List[Entity]) -> None:
        navbar = plugins.navbar.navbar.Navbar()

        for page in pages:
            navbar.add(page)

        self.plugin_context["navbar"] = navbar

    def build_output(self) -> None:
        if not self.settings.args.quiet:
            print("Building Output...")

        builder = Builder(self.importer, self.plugin_context, self.settings)
        self.create_env(builder)

        entities = self.importer.entities

        generator = builder.page_generator
        classes = [generator.class_page(ent) for ent in entities if ent.kind == "class"]
        structs = [generator.class_page(ent) for ent in entities if ent.kind == "struct"]
        examples = [generator.example_page(ent) for ent in entities if ent.kind == "example"]
        page_pages = [generator.page_page(ent) for ent in entities if ent.kind == "page"]
        namespaces = [generator.namespace_page(ent) for ent in entities if ent.kind == "namespace"]

        special_list = plugins.list_specials.list_specials.define_page(self.importer, builder)

        pages = classes + structs + page_pages + examples + namespaces + [special_list]

        # Build lookup from entities to their pages
        entity2page = {e: page for page in pages for e in page.entities}

        index = self.importer.get_entity("indexpage")
        indexpage = entity2page[index]

        self.create_navbar([indexpage, special_list])

        for i, page in enumerate(pages):
            progressbar(i + 1, len(pages))
            # print("Rendering entity " + page.primary_entity.name)
            generator.generate(page)

    def create_env(self, builder_obj: Builder) -> None:
        filters = {
            "markup": builder.layout.markup,
            "description": builder.layout.description,
            "linked_text": builder.layout.linked_text,
            "ref_explicit": builder.layout.ref_explicit,
            "ref_entity": builder.layout.ref_entity,
        }
        builder_obj.add_filters(filters)

    def generate(self, args) -> None:

        self.settings.args = args

        args.verbose = args.verbose and (not args.quiet)

        if self.settings.args.verbose:
            print("Running...")

        if args.resources:
            self.load_plugins()
            self.copy_resources()
            return

        self.load_plugins()

        self.copy_resources()

        self.read_prefs()
        self.read_external()

        # Finding xml input
        self.scan_input()

        # doxyspecial.gather_specials()

        # Building output
        self.build_output()

        # doxyspecial.build_specials()

        # Done


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate HTML from Doxygen\'s XML output')
    parser.add_argument("-r", "--resources", help="Copy Resources Only", action="store_true")
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    parser.add_argument("-q", "--quiet", help="Quiet output", action="store_true")

    args = parser.parse_args()

    DoxyDoc().generate(args)
