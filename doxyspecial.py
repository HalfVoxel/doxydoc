from doxybase import *

def build_specials ():
    print ("Building Special Pages...")
    for k,obj in DocState._docobjs.iteritems():
        if obj.kind == "special":
            if not hasattr (obj,"generator"):
                print ("Special " + obj.name + " missing required 'generator' function")
                continue

            obj.generator (obj)

def gather_specials ():
    # Clases Page
    obj = DocObj()
    obj.kind = "special"
    obj.compound = None
    obj.id = "classes";
    obj.name = "classes";
    obj.briefdescription = "Listing of all classes"
    obj.detaileddescription = ""
    obj.path = "classes"
    #Generator function required for special pages
    obj.generator = generate_classes_page
    DocState.add_docobj(obj)

    navitem = NavItem()
    navitem.label = "Classes"
    navitem.ref = obj
    DocState.navitems.append (navitem)


def generate_classes_page (obj):

    DocState.pushwriter()
    DocState.currentobj = obj


    DocState.writer.element ("p", "Listing of all classes")

    f = file(obj.full_path(), "w")
    s = DocState.popwriter()
    f.write (s)
    f.close()


DocState.add_event (2500, gather_specials)
DocState.add_event (3100, build_specials)