# from doxybase import *
from os import listdir
from os.path import isfile, isdir, join
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
from typing import Any, List
# import doxyspecial
import argparse
# import plugins.list_specials.list_specials
# import plugins.navbar.navbar


class DoxyDoc:

    def __init__(self) -> None:
        self.importer = Importer()
        self.settings = None  # type: builder.settings.Settings
        self.plugin_context = {}  # type: Dict[str,Any]
        self.plugins = []

    def load_plugins(self) -> None:

        if not self.settings.args.quiet:
            print("Loading plugins...")

        dirs = ["plugins", "themes"]
        self.plugins = []

        for dir in dirs:
            plugins = [f for f in listdir(dir) if isdir(join(dir, f)) and f not in self.settings.disabled_plugins]

            for plugin in plugins:
                self.settings.template_dirs.append(join(dir, plugin, "templates"))

                module_path = dir + "." + plugin
                __import__(module_path)

        module = __import__("plugins")
        print("Checking " + str(module))
        for k, v in module.__dict__.items():
            if isinstance(v, types.ModuleType) and hasattr(v, "Plugin"):
                print(k)
                try:
                    config = {}
                    if k in self.settings.plugins:
                        config = self.settings.plugins[k]
                    plugin = v.Plugin(config)
                    print("Loading plugin: " + str(k))
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

    def find_xml_files(self, path: str) -> List[str]:
        return [join(path, f) for f in listdir(path)
                if isfile(join(path, f)) and f.endswith(".xml")]

    def scan_input(self) -> None:
        if not self.settings.args.quiet:
            print("Scanning input...")

        self.importer.read(self.find_xml_files("input/xml"))

    def build_output(self) -> None:
        if not self.settings.args.quiet:
            print("Building output...")

        builder = Builder(self.importer, self.plugin_context, self.settings)
        self.create_env(builder)

        entities = self.importer.entities

        generator = builder.page_generator
        classes = [generator.class_page(ent) for ent in entities if isinstance(ent, ClassEntity)]
        examples = [generator.example_page(ent) for ent in entities if isinstance(ent, ExampleEntity)]
        groups = [generator.group_page(ent) for ent in entities if isinstance(ent, GroupEntity)]
        page_pages = [generator.page_page(ent) for ent in entities if isinstance(ent, PageEntity)]
        namespaces = [generator.namespace_page(ent) for ent in entities if isinstance(ent, NamespaceEntity)]

        pages = classes + page_pages + examples + namespaces + groups
        for plugin in self.plugins:
            pages = pages + plugin.define_pages(self.importer, builder)

        # Build lookup from entities to their pages
        entity2page = {e: page for page in pages for e in page.entities}

        for plugin in self.plugins:
            plugin.on_pre_build_html(self.importer, builder, entity2page)

        for i, page in enumerate(pages):
            progressbar(i + 1, len(pages))
            if self.settings.page_whitelist is None or page.path in self.settings.page_whitelist:
                # print("Rendering entity " + page.primary_entity.name)
                generator.generate(page)

        search_items = []
        for ent in entities:
            if isinstance(ent, ClassEntity):
                search_items.append({
                    "url": ent.path.full_url(),
                    "name": ent.name,
                    "fullname": ent.name,
                    "boost": self.search_boost(None, ent),
                })

                for m in ent.all_members:
                    if m.name == ent.name:
                        # Probably a constructor. Ignore those in the search results
                        continue

                    if m.defined_in_entity != ent:
                        # Inherited member, ignore in search results
                        continue

                    search_item = {
                        "url": m.path.full_url(),
                        "name": m.name,
                        "fullname": self.search_full_name(ent, m),
                        "boost": self.search_boost(ent, m),
                    }
                    search_items.append(search_item)

            if isinstance(ent, PageEntity):
                search_items.append({
                    "url": ent.path.full_url(),
                    "name": ent.name,
                    "fullname": ent.name,
                    "boost": 1,
                })

            if isinstance(ent, GroupEntity):
                search_items.append({
                    "url": ent.path.full_url(),
                    "name": ent.name,
                    "fullname": ent.name,
                    "boost": 1,
                })

        f = open("html/search_data.json", "w")
        f.write(json.dumps(search_items))
        f.close()

    def search_full_name(self, parent: ClassEntity, ent: MemberEntity) -> str:
        result = parent.name + "." + ent.name
        if ent.hasparams:
            params = []
            for param in ent.params:
                ctx = WritingContext(self.importer).with_link_stripping()
                buffer = StrTree()
                builder.layout.markup(ctx, param.type, buffer)
                params.append(str(buffer).replace(" ", ""))

            result += "(" + ",".join(params) + ")"
        return result

    def search_boost(self, parent: Entity, ent: Entity) -> float:
        boost = 100
        if isinstance(ent, ClassEntity):
            boost *= 2.0
        elif isinstance(ent, NamespaceEntity):
            boost *= 1.5
        elif isinstance(ent, PageEntity):
            boost *= 2.0
        elif isinstance(ent, ExternalEntity):
            boost *= 0.5

        if ent.protection == "private":
            boost *= 0.5
        elif ent.protection == "package":
            boost *= 0.6
        elif ent.protection == "protected":
            boost *= 0.8

        return boost

    def create_env(self, builder_obj: Builder) -> None:
        filters = {
            "markup": builder.layout.markup,
            "description": builder.layout.description,
            "linked_text": builder.layout.linked_text,
            "ref_explicit": builder.layout.ref_explicit,
            "ref_entity": builder.layout.ref_entity,
            "match_external_ref": builder.layout.match_external_ref,
            "log": lambda c, v, b: print(v)
        }
        builder_obj.add_filters(filters)

    def generate(self, args) -> None:
        try:
            config = json.loads(open(args.config).read())
        except Exception as e:
            print("Could not read configuration at '" + args.config + "'\n" + str(e))
            exit(1)

        self.settings = builder.settings.Settings(config)
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
