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

def try_call_function(name, arg):
    try:
        methodToCall = getattr(doxyext, name)
    except AttributeError:
        return None, False

    result = methodToCall(arg)
    return result, True

def register_compound(xml):

    obj = DocObj()

    obj.id = xml.get("id")
    obj.kind = xml.get("kind")
    # Will only be used for debugging if even that. Formatted name will be added later
    obj.name = xml.find("compoundname").text
    # Format path. Use - instead of :: in path names(more url friendly)
    obj.path = obj.name.replace("::", "-")

    DocState.add_docobj(obj)
    xml.set("docobj", obj)

    #Workaround for doxygen apparently generating refid:s which do not exist as id:s
    id2 = obj.id + "_1" + obj.id
    #if id2 in docobjs:
    #    print "Warning: Overwriting id " + id2

    DocState.add_docobj(obj, id2)

    ids = xml.findall(".//*[@id]")

    parent = obj

    for idnode in ids:

        obj, ok = try_call_function("parseid_" + idnode.tag, idnode)
        if not ok:
            obj = DocObj()
            obj.id = idnode.get("id")
            obj.kind = idnode.get("kind")

            #print(idnode.get("id"))
            namenode = idnode.find("name")

            if namenode is not None:
                obj.name = namenode.text
            else:
                obj.name = "<undefined " + idnode.tag + "-" + obj.id + " >"

            obj.anchor = obj.name

        if obj is not None:
            obj.compound = parent

            idnode.set("docobj", obj)
            DocState.add_docobj(obj)
            #print(obj.full_url())

    #print(docobjs)

def load_plugins():

    print("Loading Plugins...")

    plugList = [f for f in listdir("themes") if isdir(join("themes", f))]

    for moduleName in plugList:
        mFile, mPath, mDescription = imp.find_module(os.path.basename(moduleName), ["themes"])
        mObject = imp.load_module(moduleName, mFile, mPath, mDescription)
        print("Loading Theme: " + moduleName)

        try:
            obj = getattr(mObject, "tiny")
            print("Loading Tiny Overrides...")
            for k, v in obj.__dict__.iteritems():
                if not k.startswith("_"):
                    setattr(doxytiny, k, v)
        except AttributeError:
            pass

        try:
            obj = getattr(mObject, "layout")
            print("Loading Layout Overrides...")
            for k, v in obj.__dict__.iteritems():
                if not k.startswith("_"):
                    setattr(doxylayout, k, v)
        except AttributeError:
            pass

        try:
            obj = getattr(mObject, "compound")
            print("Loading Compound Overrides...")
            for k, v in obj.__dict__.iteritems():
                if not k.startswith("_"):
                    setattr(doxylayout, k, v)
        except AttributeError:
            pass

def read_external():
    print("Reading exteral")
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
    print("Copying resources")

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

    print("Scanning input")

    compounds = DocState.compounds = []
    roots = DocState.roots = []

    i = 0
    for fname in filenames:
        try:
            extension = splitext(fname)[1]

            progressbar(i + 1, len(filenames))

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
                register_compound(compound)
        except Exception as e:
            print(fname)
            raise e
        i += 1

def process_references():
    print("\nProcessing References...")

    roots = DocState.roots

    i = 0
    for root in roots:
        progressbar(i + 1, len(roots))

        process_references_root(root)
        i += 1

def process_compounds():
    print("\nProcessing Compounds...")

    compounds = DocState.compounds

    i = 0
    for compound in compounds:
        progressbar(i + 1, len(compounds))

        gather_compound_doc(compound)
        i += 1

def build_compound_output():
    print("\nBuilding Output...")

    compounds = DocState.compounds

    i = 0
    for compound in compounds:
        progressbar(i + 1, len(compounds))

        generate_compound_doc(compound)
        i += 1

def main():

    print("Running...")

    parser = argparse.ArgumentParser(description='Build the A* Pathfinding Project Packages.')
    parser.add_argument("-r", "--resources", help="Copy Resources Only", action="store_true")

    args = parser.parse_args()

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

    DocState.add_event(2500, pre_output)

    DocState.add_event(3000, build_compound_output)

    DocState.add_event(3100, doxyspecial.build_specials)

    while(DocState.next_event()):
        print("Next Event")
        pass

    #return


    #print("\nTesting References...")
    #test_id_ref(join("xml", "index.xml"))

    #print("\nPreprocessing Output...")

if __name__ == "__main__":
    print("Stuff")
    main()
