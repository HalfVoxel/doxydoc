import xml.etree.cElementTree as ET
# from doxybase import *
from os import listdir
from os.path import isfile, isdir, join
from progressbar import progressbar
import doxycompound
from doxysettings import DocSettings
from doxybase import DocState, ExternalEntity
import doxypages
import shutil
import os
import doxylayout
# import doxyspecial
import argparse


class DoxyDoc:

    def __init__(self):
        self.settings = DocSettings()
        self.state = DocState()
        self.state.settings = self.settings
        self.settings.outdir = "html"

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
        #                     if (hasattr(doxylayout, k)):
        #                         setattr(doxylayout, "_base_" + k, getattr(doxylayout, k))
        #                     setattr(doxylayout, k, v)
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
                self.state.add_docobj(obj)

        f.close()

    def test_id_ref(self, path):

        dom = ET.parse(path)

        root = dom.getroot()

        refs = root.findall(".//*[@refid]")
        for i, ref in enumerate(refs):
            progressbar(i + 1, len(refs))

            # id = ref.get("refid")
            refobj = ref.get("ref")
            assert refobj
            # print("Referenced " + refobj.name)

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

                    target_dir = os.path.join(self.settings.outdir, dstroot)
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

                target_dir = os.path.join(self.settings.outdir, dstroot)
                try:
                    os.makedirs(target_dir)
                except:
                    pass

                for fn in files:
                    source_path = os.path.join(root, fn)
                    target_path = os.path.join(target_dir, fn)
                    shutil.copy2(source_path, target_path)

            # shutil.copytree("resources", self.settings.outdir)
        except OSError:  # python >2.5
            print("No resources directory found")
            raise

    def read_prefs(self):
        if not self.settings.args.quiet:
            print ("Reading resources...")

    def find_xml_files(self):
        return [f for f in listdir("xml") if isfile(join("xml", f))]

    def scan_input(self):
        filenames = self.find_xml_files()

        if not self.settings.args.quiet:
            print("Scanning input")

        input_xml = []
        roots = []

        for i, fname in enumerate(filenames):
            progressbar(i + 1, len(filenames))

            try:
                extension = os.path.splitext(fname)[1]

                if extension != ".xml":
                    continue

                dom = ET.parse(os.path.join("xml", fname))

                assert dom is not None, "No DOM"

                root = dom.getroot()

                roots.append(root)

                compound = root.find("compounddef")

                assert root is not None, "No Root"

                if compound is not None:
                    input_xml.append(compound)
                    self.state.register_compound(compound)
            except Exception as e:
                print(fname)
                raise e

        self.state.roots = roots
        self.state.input_xml = input_xml

    def gather_entity_info(self):
        if not self.settings.args.quiet:
            print("Processing Entities...")

        entities = self.state.entities
        for i, entity in enumerate(entities):
            progressbar(i + 1, len(entities))
            doxycompound.gather_entity_doc(entity)

    def process_references(self):
        if not self.settings.args.quiet:
            print("Processing References...")

        roots = self.state.roots

        for i, root in enumerate(roots):
            progressbar(i + 1, len(roots))

            doxycompound.process_references_root(root, self.state)

    def build_output(self):
        pages = self.state.pages

        if not self.settings.args.quiet:
            print("Building Output...")

        entities = self.state.entities

        generator = doxypages.PageGenerator()
        classes = [generator.class_page(ent) for ent in entities if ent.kind == "class"]
        examples = [generator.example_page(ent) for ent in entities if ent.kind == "example"]
        page_pages = [generator.page_page(ent) for ent in entities if ent.kind == "page"]

        # Copy parent mappings
        # for page in page_pages:
        #    if page.primary_entity.parent is not None:
        #        page.parent = page.primary_entity.parent.path.page

        # pages = classes + page_pages + examples
        pages = page_pages

        for i, page in enumerate(pages):
            progressbar(i + 1, len(pages))

            generator.generate(page, self.state)

    def create_env(self):
        filters = {
            "markup": doxylayout.markup,
            "description": doxylayout.description,
            "linked_text": doxylayout.linked_text
        }
        self.state.create_template_env("templates", filters)

    def generate(self, args):

        self.settings.args = args

        args.verbose = args.verbose and (not args.quiet)

        if self.settings.args.verbose:
            print("Running...")

        if args.resources:
            self.load_plugins()
            self.copy_resources()
            return

        # filenames = ["xml/class_a_i_path.xml"]

        # Events:
        # 0    - 999    Initializaton
        self.load_plugins()

        self.copy_resources()

        self.read_prefs()
        self.read_external()

        self.create_env()
        # Finding xml input
        self.scan_input()

        # Reading and structuring data
        self.process_references()

        self.gather_entity_info()

        # doxyspecial.gather_specials()

        doxycompound.pre_output()

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
