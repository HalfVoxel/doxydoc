import xml.etree.cElementTree as ET
from doxybase import *
import doxyext
from os import listdir
from os.path import isfile, join,splitext
from progressbar import *
from doxycompound import *
from cStringIO import StringIO
import shutil
import os

def try_call_function (name, arg):
    try:
        methodToCall = getattr(doxyext, name)
    except AttributeError:
        return None, False

    result = methodToCall(arg)
    return result, True

def register_compound (xml):

    obj = DocObj ()
    obj.kind = xml.get("kind")

    obj.id = xml.get("id")
    
    obj.name = xml.find("compoundname").text
    obj.data = None
    obj.path = obj.name.replace ("::","-")

    #dump(obj)

    docobjs[obj.id] = obj

    #Workaround for doxygen apparently generating refid:s which do not exist as id:s
    id2 = obj.id + "_1" + obj.id
    print ("Generating " + id2)
    docobjs[id2] = obj

    ids = xml.findall (".//*[@id]")
    
    parent = obj

    for idnode in ids:

        obj, ok = try_call_function ("parseid_"+idnode.tag, idnode)
        if not ok:
            obj = DocObj ()
            obj.id = idnode.get("id")
            #print (idnode.get("id"))
            namenode = idnode.find("name")

            if namenode != None:
                obj.name = namenode.text
            else:
                obj.name = "<undefined " + idnode.tag + "-" + obj.id + " >"

            obj.anchor = obj.name

        if obj != None:
            obj.compound = parent
            docobjs[obj.id] = obj
            #print (obj.full_url())

    #print (docobjs)

def read_external ():

    try:
        f = open ("external.csv")
    except:
        print "Noes"

    for line in f:
        arr = line.split (",")
        if len(arr) >= 2:
            name = "__external__" + arr[0].strip()
            url = arr[1].strip()
            obj = DocObj()
            obj.id = name
            obj.name = name
            obj.exturl = url
            docobjs[obj.id] = obj

    f.close ()

def test_id_ref (path):
    
    dom = ET.parse(path)

    root = dom.getroot()

    refs = root.findall (".//*[@refid]")
    print("\nTesting References...")
    for i in range(1,len(refs)):
        ref = refs[i]
        progressbar (i+1,len(refs))

        id = ref.get("refid")
        refobj = docobjs[id]
        assert refobj
        #print ("Referenced " + refobj.name)

def main ():

    #filenames = ["xml/class_a_i_path.xml"]

    print ("Copying resources")

    try:
        resbase = "resources"
        for root,dirs,files in os.walk (resbase):
            dstroot = root.replace (resbase+"/", "")
            dstroot = dstroot.replace (resbase, "")

            try:
                os.makedirs (os.path.join("html", dstroot))
            except:
                pass

            for fn in files:
                fn2 = os.path.join(root, fn)
                print (fn2)
                shutil.copy2 (fn2, os.path.join(os.path.join("html", dstroot), fn))

        #shutil.copytree("resources", "html")
    except OSError as exc: # python >2.5
        print ("No resources directory found")
        raise

    header = file ("resources/header.html")
    DocSettings.header = header.read()

    footer = file ("resources/footer.html")
    DocSettings.footer = footer.read()

    print ("Reading exteral")
    read_external ()

    filenames = [ f for f in listdir("xml") if isfile(join("xml",f)) ]


    print ("Scanning input")

    for i in range(0,len(filenames)):
        try:
            fname = filenames[i]

            extension = splitext(fname)[1]

            progressbar (i+1,len(filenames))

            if extension != ".xml":
                continue

            dom = ET.parse(join("xml",fname))

            root = dom.getroot()

            compound = root.find("compounddef")
            if compound != None:
                register_compound (compound)

        except Exception as e:
            print (fname)
            raise e

    

    test_id_ref (join("xml", "index.xml"))

    print("\nBuilding docs...")

    for i in range(0,len(filenames)):
        fname = filenames[i]

        extension = splitext(fname)[1]

        progressbar (i+1,len(filenames))

        if extension != ".xml":
            continue

        dom = ET.parse(join("xml",fname))

        root = dom.getroot()

        compound = root.find("compounddef")
        if compound != None:
            generate_compound_doc (compound)

main ()