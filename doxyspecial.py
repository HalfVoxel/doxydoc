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

    ######
    navitem = NavItem()
    navitem.label = "Classes"
    navitem.order = 5
    navitem.ref = obj
    DocState.navitems.append(navitem)

    # Index Page
    navitem = NavItem()
    navitem.label = "Home"
    navitem.order = 0
    navitem.ref = DocState.get_docobj("indexpage")
    DocState.navitems.append(navitem)

    # Index Page
    navitem = NavItem()
    navitem.label = "Pages"
    navitem.order = 2
    navitem.ref = DocState.get_docobj("page-listing")
    DocState.navitems.append(navitem)

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
