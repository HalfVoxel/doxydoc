from doxybase import *
import doxylayout

def build_specials():
    print("Building Special Pages...")
    for k, obj in DocState._docobjs.iteritems():
        if obj.kind == "special":
            if not hasattr(obj, "generator"):
                print("Special " + obj.name + " missing required 'generator' function")
                continue

            obj.generator(obj)

def gather_specials():
    # Clases Page
    obj = DocObj()
    obj.kind = "special"
    obj.compound = None
    obj.id = "classes"
    obj.name = "classes"
    obj.briefdescription = "Listing of all classes"
    obj.detaileddescription = ""
    obj.path = "classes"

    #Generator function required for special pages
    obj.generator = generate_classes_page
    DocState.add_docobj(obj)

    # Add navigation item
    navitem = NavItem()
    navitem.label = "Classes"
    navitem.order = 5
    navitem.ref = obj
    DocState.navitems.append(navitem)

    # Pages Page
    obj = DocObj()
    obj.kind = "special"
    obj.compound = None
    obj.id = "page-listing"
    obj.name = "Pages"
    obj.briefdescription = "Listing of all pages"
    obj.detaileddescription = ""
    obj.path = "pages"

    #Generator function required for special pages
    obj.generator = generate_pages_page
    DocState.add_docobj(obj)

    # Add navigation item
    navitem = NavItem()
    navitem.label = "Pages"
    navitem.order = 2
    navitem.ref = obj
    DocState.navitems.append(navitem)

    # Index Page
    # Add navigation item
    navitem = NavItem()
    navitem.label = "Home"
    navitem.order = 0
    navitem.ref = DocState.get_docobj("indexpage")
    DocState.navitems.append(navitem)
    
    gather_examples_page()

def gather_examples_page():

    anyExamples = False
    for k, obj in DocState._docobjs.iteritems():
        if obj.kind == "example":
            anyExamples = True
            break

    if not anyExamples:
        return

    # Examples Page
    obj = DocObj()
    obj.kind = "special"
    obj.compound = None
    obj.id = "examples-listing"
    obj.name = "Examples"
    obj.briefdescription = "Listing of all examples"
    obj.detaileddescription = ""
    obj.path = "examples"

    #Generator function required for special pages
    obj.generator = generate_examples_page
    DocState.add_docobj(obj)

    # Add navigation item
    navitem = NavItem()
    navitem.label = "Examples"
    navitem.order = 5
    navitem.ref = obj
    DocState.navitems.append(navitem)

def generate_examples_page(obj):
    DocState.pushwriter()
    DocState.currentobj = obj

    doxylayout.header()
    doxylayout.navheader()

    doxylayout.begin_content()
    if obj.briefdescription is not None:
        DocState.writer.element("p", obj.briefdescription)
    if obj.detaileddescription is not None:
        DocState.writer.element("p", obj.detaileddescription)

    #doxylayout.examples_list_inner()
    DocState.writer.element("ul", None, {"class": "examples-list"})
    for k, o in DocState._docobjs.iteritems():
        if o.kind == "example":
            DocState.writer.element("li", lambda: doxylayout.docobjref(o))

    DocState.writer.element("/ul")

    doxylayout.end_content()

    doxylayout.footer()

    print ("Generating examples page at " + obj.full_path())
    f = open(obj.full_path(), "w")
    s = DocState.popwriter()
    f.write(s)
    f.close()

def generate_pages_page(obj):
    DocState.pushwriter()
    DocState.currentobj = obj

    doxylayout.header()
    doxylayout.navheader()

    doxylayout.begin_content()
    DocState.writer.element("p", "Listing of all pages")

    doxylayout.page_list_inner(None)

    doxylayout.end_content()

    doxylayout.footer()

    f = open(obj.full_path(), "w")
    s = DocState.popwriter()
    f.write(s)
    f.close()

def generate_classes_page(obj):

    DocState.pushwriter()
    DocState.currentobj = obj

    doxylayout.header()
    doxylayout.navheader()

    doxylayout.begin_content()
    DocState.writer.element("p", "Listing of all classes")

    doxylayout.namespace_list_inner(obj)

    doxylayout.end_content()

    doxylayout.footer()

    f = open(obj.full_path(), "w")
    s = DocState.popwriter()
    f.write(s)
    f.close()


DocState.add_event(2500, gather_specials)
DocState.add_event(3100, build_specials)
