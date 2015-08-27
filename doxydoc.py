# from doxybase import *
from os import listdir
from os.path import isfile, isdir, join
from progressbar import progressbar
from importer import Importer
from importer.entities import ExternalEntity
import shutil
import os
import builder.layout
from builder import Builder
import builder.settings
# import doxyspecial
import argparse


class DoxyDoc:

    def __init__(self):
        self.importer = Importer()
        self.settings = builder.settings.Settings()
        self.settings.out_dir = "html"
        self.settings.template_dir = "templates"

    def load_plugins(self):

        if not self.settings.args.quiet:
            print("Loading Plugins...")

        # dirs = ["plugins", "themes"]

        # for dir in dirs:
        #     plugins = [f for f in listdir(dir) if isdir(join(dir, f))]

        #     for moduleName in plugins:
        #         mFile, mPath, mDescription = imp.find_module(os.path.basename(moduleName), [dir])
        #         module_object = imp.load_module(moduleName, mFile, mPath, mDescription)

        #         if self.settings.args.verbose:
        #             print("Loading Theme/Plugin: " + moduleName)

        #         try:
        #             obj = getattr(module_object, "tiny")

        #             if self.settings.args.verbose:
        #                 print("\tLoading Tiny Overrides...")
        #             for k, v in obj.__dict__.iteritems():
        #                 if not k.startswith("_"):
        #                     if (hasattr(doxytiny, k)):
        #                         setattr(doxytiny, "_base_" + k, getattr(doxytiny, k))
        #                     setattr(doxytiny, k, v)
        #         except AttributeError:
        #             pass

        #         try:
        #             obj = getattr(module_object, "layout")
        #             if self.settings.args.verbose:
        #                 print("\tLoading Layout Overrides...")
        #             for k, v in obj.__dict__.iteritems():
        #                 if not k.startswith("_"):
        #                     if (hasattr(builder.layout, k)):
        #                         setattr(builder.layout, "_base_" + k, getattr(builder.layout, k))
        #                     setattr(builder.layout, k, v)
        #         except AttributeError:
        #             pass

        #         try:
        #             obj = getattr(module_object, "compound")
        #             if self.settings.args.verbose:
        #                 print("\tLoading Entity Overrides...")
        #             for k, v in obj.__dict__.iteritems():
        #                 if not k.startswith("_"):
        #                     if (hasattr(doxycompound, k)):
        #                         setattr(doxycompound, "_base_" + k, getattr(doxycompound, k))
        #                     setattr(doxycompound, k, v)
        #         except AttributeError:
        #             pass

    def read_external(self):
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
                obj = ExternalEntity()
                obj.id = "__external__" + name
                obj.kind = "external"
                obj.name = name
                obj.exturl = url
                self.importer._add_docobj(obj)

        f.close()

    def copy_resources(self):
        if not self.settings.args.quiet:
            print("Copying resources...")

        try:
            plugins = [f for f in listdir("themes") if isdir(join("themes", f))]
            for moduleName in plugins:
                resbase = os.path.join(os.path.join("themes", moduleName), "resources")
                for root, dirs, files in os.walk(resbase):
                    dstroot = root.replace(resbase + "/", "")
                    dstroot = dstroot.replace(resbase, "")

                    target_dir = os.path.join(self.settings.out_dir, dstroot)
                    try:
                        os.makedirs(target_dir)
                    except:
                        pass

                    for fn in files:
                        source_path = os.path.join(root, fn)
                        target_path = os.path.join(target_dir, fn)
                        shutil.copy2(source_path, target_path)
        except OSError:
            print("Error while copying theme resources")

        try:
            resbase = "resources"
            for root, dirs, files in os.walk(resbase):
                dstroot = root.replace(resbase + "/", "")
                dstroot = dstroot.replace(resbase, "")

                target_dir = os.path.join(self.settings.out_dir, dstroot)
                try:
                    os.makedirs(target_dir)
                except:
                    pass

                for fn in files:
                    source_path = os.path.join(root, fn)
                    target_path = os.path.join(target_dir, fn)
                    shutil.copy2(source_path, target_path)

            # shutil.copytree("resources", self.settings.out_dir)
        except OSError:  # python >2.5
            print("No resources directory found")
            raise

    def read_prefs(self):
        if not self.settings.args.quiet:
            print ("Reading resources...")

    def find_xml_files(self):
        return [join("xml", f) for f in listdir("xml")
                if isfile(join("xml", f)) and f.endswith(".xml")]

    def scan_input(self):
        if not self.settings.args.quiet:
            print("Scanning input")

        self.importer.read(self.find_xml_files())

    def build_output(self):
        if not self.settings.args.quiet:
            print("Building Output...")

        builder = Builder(self.importer, self.settings)
        self.create_env(builder)

        entities = self.importer.entities

        generator = builder.page_generator
        classes = [generator.class_page(ent) for ent in entities if ent.kind == "class"]
        examples = [generator.example_page(ent) for ent in entities if ent.kind == "example"]
        page_pages = [generator.page_page(ent) for ent in entities if ent.kind == "page"]

        # Copy parent mappings
        # for page in page_pages:
        #    if page.primary_entity.parent is not None:
        #        page.parent = page.primary_entity.parent.path.page

        pages = classes + page_pages + examples

        for i, page in enumerate(pages):
            progressbar(i + 1, len(pages))
            # print("Rendering entity " + page.primary_entity.name)
            generator.generate(page)

    def create_env(self, builder_obj):
        filters = {
            "markup": builder.layout.markup,
            "description": builder.layout.description,
            "linked_text": builder.layout.linked_text,
            "ref_explicit": builder.layout.ref_explicit
        }
        builder_obj.add_filters(filters)

    def generate(self, args):

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
