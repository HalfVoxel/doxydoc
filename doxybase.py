from pprint import pprint
from xml.sax.saxutils import escape
from heapq import *
import types
import doxyext
from doxysettings import DocSettings
import jinja2

def try_call_function(name, arg):
    try:
        methodToCall = getattr(doxyext, name)
    except AttributeError:
        return None, False

    result = methodToCall(arg)
    return result, True

FILE_EXT = ".html"
OUTPUT_DIR = "html"

docobjs = {}

# escape() and unescape() takes care of &, < and >.
html_escape_table = {
    '"': "&quot;",
    "'": "&apos;"
}
html_unescape_table = {v: k for k, v in html_escape_table.items()}

def paramescape(v):
    return escape(v, html_escape_table)

class StringBuilder:

    def __init__(self):
        self.arr = []

    def __add__(self, t):
        assert t is not None
        self.arr.append(escape(t))
        return self

    def __iadd__(self, t):
        assert t is not None
        self.arr.append(escape(t))
        return self

    def html(self, t):
        assert t is not None
        self.arr.append(t)
        return self

    #def element(self, t, c):
    #    assert t is not None
    #    assert c is not None
    #    self.arr.append("<" + t + ">" + escape(t) + "</" + t + ">")

    def element(self, t, c=None, params=None):
        assert t
        if params is None:
            self.arr.append("<" + t + ">")
        else:
            self.arr.append("<" + t + " ")
            for k, v in params.iteritems():
                if v is not None and v != "":
                    self.arr.append(k + "='" + paramescape(v) + "' ")

            self.arr.append(">")
        
        if c is not None:
            if isinstance(c, types.FunctionType):
                c()
            else:
                self.arr.append(escape(c))

            self.arr.append("</" + t + ">")

    def elem(self, t):
        assert t is not None
        self.arr.append("<" + t + ">")

    def __str__(self):
        cache = ''.join(self.arr)
        del self.arr[:]
        self.arr.append(cache)
        return cache

    def clear(self):
        del self.arr[:]

class StringBuilderPlain:

    def __init__(self):
        self.arr = []

    def __add__(self, t):
        assert t is not None
        self.arr.append(t)
        return self

    def __iadd__(self, t):
        assert t is not None
        self.arr.append(t)
        return self

    def html(self, t):
        assert t is not None
        self.arr.append(t)
        return self

    #def element(self, t, c):
    #    assert t is not None
    #    assert c is not None
    #    self.arr.append("<" + t + ">" + escape(t) + "</" + t + ">")

    def element(self, t, c=None, params=None):
        assert t
        if c is None:
            return

        if isinstance(c, types.FunctionType):
            c()
        else:
            self.arr.append(c)

    def elem(self, t):
        assert t is not None

    def __str__(self):
        cache = ''.join(self.arr)
        del self.arr[:]
        self.arr.append(cache)
        return cache

    def clear(self):
        del self.arr[:]

class DocState:
    _stack = []
    writer = StringBuilder()
    currentobj = None
    navitems = []

    pages = []
    roots = None
    input_xml = None
    environment = None
    _filters = []

    ''' Prevents infinte loops of tooltips in links by disabling links after a certain depth '''
    depth_ref = 0

    _events = []
    _docobjs = {}
    
    _trigger_heaps = {}

    _usedPaths = set()

    @staticmethod
    def add_filter(name, func):
        DocState._filters.append((name, func))

    @staticmethod
    def create_template_env(dir):
        DocState.environment = jinja2.Environment(loader=jinja2.FileSystemLoader(dir))
        for name, func in DocState._filters:
            DocState.environment.filters[name] = func

    @staticmethod
    def iter_unique_docobjs():
        for k, v in DocState._docobjs.iteritems():
            if k == v.id:
                yield v

    @staticmethod
    def add_docobj(obj, id=None):
        assert hasattr(obj, "name"), "DocObjects must have names"
        assert hasattr(obj, "kind"), "DocObjects must have kinds"
        assert hasattr(obj, "id"), "DocObjects must have ids"
        if id is None:
            id = obj.id
        DocState._docobjs[id] = obj
    
    @staticmethod
    def has_docobj(id):
        return id in DocState._docobjs

    @staticmethod
    def get_docobj(id):
        return DocState._docobjs[id]

    @staticmethod
    def trigger_listener(name, priority, callback):
        assert callback
        assert name

        if DocSettings.args.verbose:
            print ("Adding listener for " + name + " with priority " + priority)

        if not name in DocState._trigger_heaps:
            DocState._trigger_heaps[name] = []

        DocState._trigger_heaps[name].append((priority, callback))
        DocState._trigger_heaps[name].sort(key=lambda tup: tup[0])

    @staticmethod
    def trigger(name):

        if not name in DocState._trigger_heaps:
            return

        events = DocState._trigger_heaps[name]

        for event in events:
            event[1]()

    @staticmethod
    def add_event(priority, callback):
        heappush(DocState._events, (priority, callback))

    @staticmethod
    def next_event():
        try:
            prio, callback = heappop(DocState._events)
        except IndexError:
            return False

        callback()
        return True

    @staticmethod
    def empty_writerstack():
        return len(DocState._stack) is 0

    ''' Push a new writer.
        Call #popwriter to remove the writer and get the resulting written string.
    '''
    @staticmethod
    def pushwriter():
        if DocState.writer is not None:
            DocState._stack.append(DocState.writer)
        DocState.writer = StringBuilder()

    ''' Pushes a new writer which will not write html elements.
        Exception is the html() function which will function as outputting plain text
    '''
    @staticmethod
    def pushwriterplain():
        if DocState.writer is not None:
            DocState._stack.append(DocState.writer)
        DocState.writer = StringBuilderPlain()

    @staticmethod
    def popwriter():
        s = str(DocState.writer)
        if DocState.empty_writerstack():
            DocState.writer.clear()
        else:
            DocState.writer = DocState._stack.pop()
        return s

    ''' Register a page with a docobj and xml node.
        Assumed to be a node in a previously found compound xml file
    '''
    @staticmethod
    def register_page(obj, xml):
        obj.path = obj.name.replace("::", "-")
        obj.anchor = None

        DocState.pages.append(obj)

        counter = 1
        while (obj.path + ("" if counter == 1 else str(counter))) in DocState._usedPaths:
            counter += 1

        if counter > 1:
            obj.path = obj.path + str(counter)

        DocState._usedPaths.add(obj.path)

        DocState.add_docobj(obj)

        ids = xml.findall(".//*[@id]")

        parent = obj

        # Set all child nodes to refer to this page instead of the original page
        for idnode in ids:

            obj = idnode.get("docobj")

            if obj is not None:
                obj.compound = parent
    
    @staticmethod
    def register_compound(xml):

        obj = DocObj()

        DocState.pages.append(obj)
        obj.id = xml.get("id")
        obj.kind = xml.get("kind")
        # Will only be used for debugging if even that. Formatted name will be added later
        obj.name = xml.find("compoundname").text
        # Format path. Use - instead of :: in path names (more url friendly)
        obj.path = obj.name.replace("::", "-")
        #obj.path = obj.name.replace(".", "-")

        counter = 1
        while (obj.path + ("" if counter == 1 else str(counter))) in DocState._usedPaths:
            counter += 1

        if counter > 1:
            obj.path = obj.path + str(counter)

        DocState._usedPaths.add(obj.path)

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

class DocMember:

    pass
    
class NavItem:
    def __init__(self):
        self.label = ""
        self.obj = None
        self.url = None


class DocObj:
    def __init__(self):
        self.hidden = False
        self.name = ""
        self.id = ""

    def __str__(self):
        return "DocObj: " + self.id

    ''' Url to the page (including eventual anchor) where the DocObj exists '''
    def full_url(self):
        url = self.page_url()
        if hasattr(self, 'anchor') and self.anchor is not None:
            url += "#" + self.anchor
        return url

    ''' Url to the page where the DocObj exists '''
    def page_url(self):
        if hasattr(self, 'exturl'):
            return self.exturl

        global FILE_EXT
        if hasattr(self, 'path'):
            url = self.path + FILE_EXT
        else:
            if hasattr(self, 'compound'):
                url = self.compound.page_url()
            elif hasattr(self, 'parent'):
                url = self.parent.page_url()
            else:
                print("NO COMPOUND ON OBJECT WITHOUT PATH")
                dump(self)
                url = "<undefined>"

        return url

    def full_path(self):
        global FILE_EXT
        global OUTPUT_DIR

        if hasattr(self, 'path'):
            url = self.path + FILE_EXT
        else:
            if hasattr(self, 'compound'):
                url = self.compound.full_url()
            else:
                print("NO COMPOUND ON OBJECT WITHOUT PATH")
                dump(self)
                url = "<undefined>"

        return OUTPUT_DIR + "/" + url

def dump(obj):
    pprint(vars(obj))
