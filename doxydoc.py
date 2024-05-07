# from doxybase import *
from os import listdir
from os.path import isfile, isdir, join
import re
from custom_progressbar import progressbar as custom_progressbar
from progressbar import progressbar
from importer import Importer
from importer.entities import ExternalEntity, Entity, ClassEntity, PageEntity, NamespaceEntity, ExampleEntity, GroupEntity, MemberEntity
import shutil
import os
import builder.layout
from builder import Builder, Page, WritingContext, StrTree
import builder.settings
from subprocess import call
import json
import types
from typing import Any, List, Dict
# import doxyspecial
import argparse
# import plugins.list_specials.list_specials
# import plugins.navbar.navbar
from doxydoc_plugin import DoxydocPlugin
from search import build_search_data, description_to_string


class DoxyDoc:

    def __init__(self) -> None:
        self.importer = Importer()
        self.settings = None  # type: builder.settings.Settings
        self.plugin_context = {}  # type: Dict[str,Any]
        self.plugins = []  # type: List[DoxydocPlugin]

    def load_plugins(self) -> None:

        if not self.settings.args.quiet:
            print("Loading plugins...")

        dirs = ["plugins", "themes"]
        self.plugins = []

        for dir in dirs:
            plugins = [f for f in listdir(dir) if isdir(join(dir, f)) and f not in self.settings.disabled_plugins]

            for pluginName in plugins:
                self.settings.template_dirs.append(join(dir, pluginName, "templates"))

                module_path = dir + "." + pluginName
                __import__(module_path)

        module = __import__("plugins")
        for k, v in module.__dict__.items():
            if isinstance(v, types.ModuleType) and hasattr(v, "Plugin"):
                try:
                    config = {}  # type: Dict[str, Any]
                    if k in self.settings.plugins:
                        config = self.settings.plugins[k]
                    plugin = getattr(v, "Plugin")(config)  # type: DoxydocPlugin
                    self.plugins.append(plugin)
                    self.plugin_context[str(k)] = plugin
                except Exception as e:
                    print(e)
                    pass
                # print(v.__dict__)


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

                target_dir2 = os.path.join(target_dir, dstroot)
                try:
                    os.makedirs(target_dir2)
                except:
                    pass

                for fn in files:
                    source_path = os.path.join(root, fn)
                    target_path = os.path.join(target_dir2, fn)

                    if source_path.endswith(".scss"):
                        target_path = target_path.replace(".scss", ".css")
                        # Process scss files using sass
                        call(["sass", os.path.realpath(source_path), os.path.realpath(target_path)])
                    else:
                        shutil.copy2(source_path, target_path)
        except OSError as e:
            print("Error while copying resources: " + str(e))

    def process_images(self, dir: str):
        print("Scaling down images")
        for root, dirs, files in progressbar(os.walk(dir)):
            for fn in files:
                source_path = os.path.join(root, fn)
                source_name, ext = os.path.splitext(source_path)
                if source_name.endswith("@2x") or source_name.endswith("@1.5x"):
                    scale = 2 if source_name.endswith("@2x") else 1.5
                    invscale = str(round(100/scale)) + "%"

                    # Remove everything after the last @
                    target_path = "@".join(source_name.split("@")[0:-1])
                    if os.path.exists(target_path + ext) or os.path.exists(target_path + "@1x" + ext):
                        # Don't bother creating a smaller variant. It seems it already exists
                        pass
                    else:
                        # Create a 1x variant of the image
                        target_path = target_path + ext
                        # print("Scaling down " + str(source_path))
                        # strip is used to remove metadata from the image, leading to a bitwise identical result every time (otherwise we get timestamps and such)
                        call(["convert", "-strip", "-scale", invscale, os.path.realpath(source_path), os.path.realpath(target_path)])


    def copy_resources(self) -> None:
        if not self.settings.args.quiet:
            print("Copying resources...")

        resource_dir = os.path.join(self.settings.out_dir, "resources")

        self.copy_resources_dir("resources", resource_dir)

        themes = [f for f in listdir("themes") if isdir(join("themes", f))]
        for moduleName in themes:
            resbase = os.path.join(os.path.join("themes", moduleName), "resources")
            self.copy_resources_dir(resbase, resource_dir)

        image_dir = os.path.join(self.settings.out_dir, "images")
        if os.path.isdir(image_dir):
            shutil.rmtree(image_dir)
        self.copy_resources_dir(os.path.join(self.settings.in_dir, "images"), image_dir)

        if self.settings.extra_css is not None:
            target_file = os.path.join(resource_dir, "style.css")
            source_file = os.path.realpath(self.settings.extra_css)

            # Process scss file
            if source_file.endswith(".scss"):
                tmp_path = "/tmp/temp_style.css"
                call(["sass", source_file, os.path.realpath(tmp_path)])
                source_file = tmp_path

            # Note: opening in append mode
            with open(target_file, "a") as f:
                f.write("\n/* Extra CSS */\n")
                f.write(open(source_file).read())

        self.process_images(image_dir)

    def find_xml_files(self, path: str) -> List[str]:
        return [join(path, f) for f in listdir(path)
                if isfile(join(path, f)) and f.endswith(".xml")]

    def scan_input(self) -> None:
        if not self.settings.args.quiet:
            print("Scanning input...")

        self.importer.read(self.find_xml_files(os.path.join(self.settings.in_dir, "xml")))

    def build_output(self) -> None:
        if not self.settings.args.quiet:
            print("Building output...")

        builder = Builder(self.importer, self.plugin_context, self.settings)
        self.create_env(builder)

        entities = self.importer.entities

        # Prime the excluded cache and output info
        for ent in entities:
            builder.default_writing_context.is_entity_excluded(ent)

        generator = builder.page_generator
        classes = [generator.class_page(ent) for ent in entities if isinstance(ent, ClassEntity)]
        examples = [generator.example_page(ent) for ent in entities if isinstance(ent, ExampleEntity)]
        groups = [generator.group_page(ent) for ent in entities if isinstance(ent, GroupEntity)]
        page_pages = [generator.page_page(ent) for ent in entities if isinstance(ent, PageEntity)]
        namespaces = [generator.namespace_page(ent) for ent in entities if isinstance(ent, NamespaceEntity)]

        pages = classes + page_pages + examples + namespaces + groups

        if self.settings.separate_function_pages:
            for ent in entities:
                if isinstance(ent, ClassEntity):
                    pages += generator.function_overload_pages(ent)

        for plugin in self.plugins:
            pages = pages + plugin.define_pages(self.importer, builder)

        # Build lookup from entities to their pages
        entity2page = {e: page for page in pages for e in page.entities}

        for plugin in self.plugins:
            plugin.on_pre_build_html(self.importer, builder, entity2page)

        build_search_data(generator.default_writing_context, entities, self.settings)

        for i, page in enumerate(pages):
            custom_progressbar(i + 1, len(pages))
            if self.settings.page_whitelist is None or page.path in self.settings.page_whitelist:
                # print("Rendering entity " + page.path)
                generator.generate(page)
        
        for plugin in self.plugins:
            plugin.on_post_build_html(self.importer, builder, entity2page)

    def create_env(self, builder_obj: Builder) -> None:
        def map_protection(ctx: WritingContext, protection: str, buffer: StrTree):
            if protection == "package":
                buffer.append("internal")
            else:
                buffer.append(protection)
        
        filters = {
            "markup": builder.layout.markup,
            "description": builder.layout.description,
            "description_with_scope": builder.layout.description_with_scope,
            "description_as_text": builder.layout.description_as_text,
            "linked_text": builder.layout.linked_text,
            "ref_explicit": builder.layout.ref_explicit,
            "ref_entity": builder.layout.ref_entity,
            "local_anchor": builder.layout.get_local_anchor,
            "ref_entity_with_contents": builder.layout.ref_entity_with_contents,
            "match_external_ref": builder.layout.match_external_ref,
            "log": lambda c, v, b: print(v),
            "map_protection_name": map_protection,
        }
        builder_obj.add_filters(filters)
        builder_obj.environment.filters["is_entity_excluded_in_output"] = builder_obj.default_writing_context.is_entity_excluded

    def generate(self, args) -> None:
        try:
            config = json.loads(open(args.config).read())
        except Exception as e:
            print("Could not read configuration at '" + args.config + "'\n" + str(e))
            exit(1)

        self.settings = builder.settings.Settings(config, os.path.dirname(args.config))
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
    parser.add_argument("-c", "--config", default="config.json", help="Path to config file", type=str)

    args = parser.parse_args()

    DoxyDoc().generate(args)
