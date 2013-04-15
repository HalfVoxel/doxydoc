from pprint import pprint
from xml.sax.saxutils import escape
from heapq import *
import types

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

class DocState:
    _stack = []
    writer = StringBuilder()
    currentobj = None
    navitems = []

    roots = None
    compounds = None

    ''' Prevents infinte loops of tooltips in links by disabling links after a certain depth '''
    depth_ref = 0

    _events = []
    _docobjs = {}

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

    @staticmethod
    def pushwriter():
        if DocState.writer is not None:
            DocState._stack.append(DocState.writer)
        DocState.writer = StringBuilder()

    @staticmethod
    def popwriter():
        s = str(DocState.writer)
        if DocState.empty_writerstack():
            DocState.writer.clear()
        else:
            DocState.writer = DocState._stack.pop()
        return s

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

    def full_url(self):

        if hasattr(self, 'exturl'):
            return self.exturl

        global FILE_EXT
        if hasattr(self, 'path'):
            url = self.path + FILE_EXT
        else:
            if hasattr(self, 'compound'):
                url = self.compound.full_url()
            else:
                print("NO COMPOUND ON OBJECT WITHOUT PATH")
                dump(self)
                url = "<undefined>"

        if hasattr(self, 'anchor'):
            url += "#" + self.anchor
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
