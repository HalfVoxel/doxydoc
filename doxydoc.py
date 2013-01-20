import xml.etree.cElementTree as ET
from doxybase import *
import doxyext
from os import listdir
from os.path import isfile, join,splitext
from progressbar import *
from doxycompound import *
from cStringIO import StringIO

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