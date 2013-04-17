import xml.etree.cElementTree as ET
from doxybase import *
import doxyext
from os import listdir
from os.path import isfile, isdir, join, splitext
from progressbar import *
from doxycompound import *
import shutil
import os
import imp
import doxytiny
import doxylayout
import doxyspecial
import argparse
import sys

def try_call_function(name, arg):
    try:
        methodToCall = getattr(doxyext, name)
    except AttributeError:
        return None, False

    result = methodToCall(arg)
    return result, True

def load_plugins():

    if not DocSettings.args.quiet:
        print("Loading Plugins...")

    dirs = ["plugins", "themes"]

    for dir in dirs:
        plugList = [f for f in listdir(dir) if isdir(join(dir, f))]

        for moduleName in plugList:
            mFile, mPath, mDescription = imp.find_module(os.path.basename(moduleName), [dir])
            mObject = imp.load_module(moduleName, mFile, mPath, mDescription)

            if DocSettings.args.verbose:
                print("Loading Theme/Plugin: " + moduleName)

            try:
                obj = getattr(mObject, "tiny")

                if DocSettings.args.verbose:
                    print("\tLoading Tiny Overrides...")
                for k, v in obj.__dict__.iteritems():
                    if not k.startswith("_"):
                        if (hasattr(doxytiny, k)):
                            setattr(doxytiny, "_base_" + k, getattr(doxytiny, k))
                        setattr(doxytiny, k, v)
            except AttributeError:
                pass

            try:
                obj = getattr(mObject, "layout")
                if DocSettings.args.verbose:
                    print("\tLoading Layout Overrides...")
                for k, v in obj.__dict__.iteritems():
                    if not k.startswith("_"):
                        if (hasattr(doxylayout, k)):
                            setattr(doxylayout, "_base_" + k, getattr(doxylayout, k))
                        setattr(doxylayout, k, v)
            except AttributeError:
                pass

            try:
                obj = getattr(mObject, "compound")
                if DocSettings.args.verbose:
                    print("\tLoading Compound Overrides...")
                for k, v in obj.__dict__.iteritems():
                    if not k.startswith("_"):
                        if (hasattr(doxycompound, k)):
                            setattr(doxycompound, "_base_" + k, getattr(doxycompound, k))
                        setattr(doxycompound, k, v)
            except AttributeError:
                pass

def read_external():
    if not DocSettings.args.quiet:
        print("Reading exteral...")

    try:
        f = open("external.csv")
    except:
        print "Noes"

    for line in f:
        arr = line.split(",")
        if len(arr) >= 2:
            name = arr[0].strip()
            url = arr[1].strip()
            obj = DocObj()
            obj.id = "__external__" + name
            obj.kind = "external"
            obj.name = name
            obj.exturl = url
            DocState.add_docobj(obj)

    f.close()

def test_id_ref(path):

    dom = ET.parse(path)

    root = dom.getroot()

    refs = root.findall(".//*[@refid]")
    for i in range(1, len(refs)):
        ref = refs[i]
        progressbar(i + 1, len(refs))

        #id = ref.get("refid")
        refobj = ref.get("ref")
        assert refobj
        #print("Referenced " + refobj.name)

def copy_resources():
    if not DocSettings.args.quiet:
        print("Copying resources...")

    try:
        plugList = [f for f in listdir("themes") if isdir(join("themes", f))]
        for moduleName in plugList:
            resbase = os.path.join(os.path.join("themes", moduleName), "resources")
            for root, dirs, files in os.walk(resbase):
                dstroot = root.replace(resbase + "/", "")
                dstroot = dstroot.replace(resbase, "")

                try:
                    os.makedirs(os.path.join("html", dstroot))
                except:
                    pass

                for fn in files:
                    fn2 = os.path.join(root, fn)
                    shutil.copy2(fn2, os.path.join(os.path.join("html", dstroot), fn))
    except OSError:
        print("Error while copying theme resources")

    try:
        resbase = "resources"
        for root, dirs, files in os.walk(resbase):
            dstroot = root.replace(resbase + "/", "")
            dstroot = dstroot.replace(resbase, "")

            try:
                os.makedirs(os.path.join("html", dstroot))
            except:
                pass

            for fn in files:
                fn2 = os.path.join(root, fn)
                shutil.copy2(fn2, os.path.join(os.path.join("html", dstroot), fn))

        #shutil.copytree("resources", "html")
    except OSError:  # python >2.5
        print("No resources directory found")
        raise

def read_prefs():

    if not DocSettings.args.quiet:
        print ("Reading resources...")

    header = None
    footer = None

    try:
        plugList = [f for f in listdir("themes") if isdir(join("themes", f))]
        for moduleName in plugList:
            resbase = os.path.join(os.path.join("themes", moduleName), "resources")
            if os.path.exists(os.path.join(resbase, "header.html")):
                header = file(os.path.join(resbase, "header.html"))

            if os.path.exists(os.path.join(resbase, "footer.html")):
                footer = file(os.path.join(resbase, "footer.html"))
    except OSError:
        print ("Error reading theme header and footer")

    if os.path.exists("resources/header.html"):
        header = file("resources/header.html")

    if os.path.exists("resources/footer.html"):
        footer = file("resources/footer.html")

    if header is None:
        print ("Could not find a header.html file in either 'resources' or a theme's 'resources' folder")
        sys.exit(1)

    if footer is None:
        print ("Could not find a footer.html file in either 'resources' or a theme's 'resources' folder")
        sys.exit(1)

    DocSettings.header = header.read()
    header.close()

    DocSettings.footer = footer.read()
    footer.close()

def scan_input():
    filenames = [f for f in listdir("xml") if isfile(join("xml", f))]

    if not DocSettings.args.quiet:
        print("Scanning input")

    compounds = DocState.input_xml = []
    roots = DocState.roots = []

    for i in xrange(0, len(filenames)):
        fname = filenames[i]

        progressbar(i + 1, len(filenames))

        try:
            extension = splitext(fname)[1]

            if extension != ".xml":
                continue

            dom = ET.parse(join("xml", fname))

            root = dom.getroot()

            roots.append(root)

            compound = root.find("compounddef")

            assert root is not None, "Root is None"
            assert dom is not None, "Dom is None"

            if compound is not None:
                compounds.append(compound)
                DocState.register_compound(compound)
        except Exception as e:
            print(fname)
            raise e

def process_references():
    if not DocSettings.args.quiet:
        print("Processing References...")

    roots = DocState.roots

    i = 0
    for i in xrange(0, len(roots)):
        progressbar(i + 1, len(roots))

        process_references_root(roots[i])

def process_compounds():
    if not DocSettings.args.quiet:
        print("Processing Compounds...")

    compounds = DocState.input_xml

    i = 0
    for compound in compounds:
        progressbar(i + 1, len(compounds))

        gather_compound_doc(compound)
        i += 1

def build_compound_output():
    if not DocSettings.args.quiet:
        print("Building Output...")

    pages = DocState.pages

    i = 0
    for page in pages:
        progressbar(i + 1, len(pages))

        generate_compound_doc(page)
        i += 1

def main():

    

    # Set default encoding to UTF-8 to avoid errors when docs have unusual characters
    reload(sys)
    sys.setdefaultencoding('UTF-8')

    parser = argparse.ArgumentParser(description='Build the A* Pathfinding Project Packages.')
    parser.add_argument("-r", "--resources", help="Copy Resources Only", action="store_true")
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    parser.add_argument("-q", "--quiet", help="Quiet output", action="store_true")

    args = parser.parse_args()

    DocSettings.args = args

    args.verbose = args.verbose and (not args.quiet)

    if DocSettings.args.verbose:
        print("Running...")

    if args.resources:
        load_plugins()
        copy_resources()
        return
        
    #filenames = ["xml/class_a_i_path.xml"]

    ## Events:
    # 0    - 999    Initializaton
    # 1000 - 1999   Reading input
    # 2000 - 2999   Structuring data
    # 3000 - 4000   Building output
    #
    DocState.add_event(200, load_plugins)

    DocState.add_event(400, copy_resources)

    DocState.add_event(600, read_prefs)
    DocState.add_event(700, read_external)

    DocState.add_event(1000, scan_input)

    DocState.add_event(2000, process_references)

    DocState.add_event(2300, process_compounds)
    DocState.add_event(2340, doxyspecial.gather_specials)

    DocState.add_event(2500, pre_output)

    DocState.add_event(3000, build_compound_output)

    DocState.add_event(3100, doxyspecial.build_specials)

    # Progress through the event heap until everything has been done
    while(DocState.next_event()):
        pass

    # Done

if __name__ == "__main__":
    main()
