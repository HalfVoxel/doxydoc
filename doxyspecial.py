from doxybase import Entity, DocState, NavItem
import doxylayout
import doxycompound


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
    obj = Entity()
    obj.kind = "special"
    obj.compound = None
    obj.id = "classes"
    obj.name = "classes"
    obj.briefdescription = "Listing of all classes"
    obj.detaileddescription = ""
    obj.path = "classes"

    # Generator function required for special pages
    obj.generator = generate_classes_page
    DocState.add_docobj(obj)

    # Add navigation item
    navitem = NavItem()
    navitem.label = "Classes"
    navitem.order = 5
    navitem.ref = obj
    DocState.navitems.append(navitem)

    # Pages Page
    obj = Entity()
    obj.kind = "special"
    obj.compound = None
    obj.id = "page-listing"
    obj.name = "Pages"
    obj.briefdescription = "Listing of all pages"
    obj.detaileddescription = ""
    obj.innerpages = doxylayout.get_inner_pages(None)
    obj.path = "pages"

    # Generator function required for special pages
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

    any_examples = any(obj.kind == "example" for obj in DocState._docobjs)

    if not any_examples:
        return

    # Examples Page
    obj = Entity()
    obj.kind = "special"
    obj.compound = None
    obj.id = "examples-listing"
    obj.name = "Examples"
    obj.briefdescription = "Listing of all examples"
    obj.detaileddescription = ""
    obj.path = "examples"

    # Generator function required for special pages
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

    result = doxylayout.StrTree()
    result += doxylayout.header()
    result += doxylayout.navheader()

    result += doxylayout.begin_content()
    if obj.briefdescription is not None:
        result.element("p", obj.briefdescription)
    if obj.detaileddescription is not None:
        result.element("p", obj.detaileddescription)

    result.element("ul", None, {"class": "examples-list"})
    for k, o in DocState._docobjs.iteritems():
        if o.kind == "example":
            result.element("li", lambda: doxylayout.docobjref(o))

    result.element("/ul")

    result += doxylayout.end_content()

    result += doxylayout.footer()

    f = open(obj.full_path(), "w")
    f.write(str(result))
    f.close()


def generate_pages_page(obj):
    DocState.currentobj = obj
    template = "special_pages_list"

    return doxycompound.write_from_template(template, obj)


def generate_classes_page(obj):
    pass
    # DocState.pushwriter()
    # DocState.currentobj = obj

    # doxylayout.header()
    # doxylayout.navheader()

    # doxylayout.begin_content()
    # DocState.writer.element("p", "Listing of all classes")

    # doxylayout.namespace_list_inner(obj)

    # doxylayout.end_content()

    # doxylayout.footer()

    # f = open(obj.full_path(), "w")
    # s = DocState.popwriter()
    # f.write(s)
    # f.close()
