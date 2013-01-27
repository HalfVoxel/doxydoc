from pprint import pprint
from xml.sax.saxutils import escape

def try_call_function (name, arg):
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
html_unescape_table = {v:k for k, v in html_escape_table.items()}

def paramescape(v):
    return escape(v, html_escape_table)

class StringBuilder:

    def __init__ (self):
        self.arr = []
        self.cache = ""

    def __add__ (self, t):
        assert t != None
        self.arr.append (escape(t))
        return self

    def __iadd__ (self, t):
        assert t != None
        self.arr.append (escape(t))
        return self

    def html (self, t):
        assert t != None
        self.arr.append (t)
        return self

    #def element (self, t, c):
    #    assert t != None
    #    assert c != None
    #    self.arr.append ("<" + t + ">" + escape(t) + "</" + t + ">")

    def element (self, t, c = None, params = None):
        assert t
        if params == None:
            self.arr.append ("<" + t + ">")
        else:
            self.arr.append ("<" + t + " ")
            for k,v in params.iteritems():
                if v != None and v != "":
                    self.arr.append (k + "='" + paramescape (v) + "' ")

            self.arr.append (">")
        
        if c != None:
            self.arr.append (escape(c))
            self.arr.append ("</" + t + ">")

    def elem (self, t):
        assert t != None
        self.arr.append ("<" + t + ">")

    def __str__ (self):
        self.cache = ''.join(self.arr)
        del self.arr[:]
        self.arr.append(self.cache)
        return self.cache

    def clear (self):
        del self.arr[:]

class DocState:
    stack = []
    writer = StringBuilder()
    compound = None

    ''' Prevents infinte loops of tooltips in links by disabling links after a certain depth '''
    depth_ref = 0

    @staticmethod
    def pushwriter ():
        if DocState.writer != None:
            DocState.stack.append (DocState.writer)
        DocState.writer = StringBuilder()

    @staticmethod
    def popwriter ():
        s = str(DocState.writer)
        if len(DocState.stack) == 0:
            DocState.writer.clear()
        else:
            DocState.writer = DocState.stack.pop()
        return s


class DocSettings:
    header = "<html>"
    footer = "</html>"
    external = {}

class DocMember:

    pass
    
class DocObj:
    
    def __str__ (self):
        return "DocObj: " + self.id

    def full_url (self):

        if hasattr(self,'exturl'):
            return self.exturl

        global FILE_EXT
        if hasattr(self,'path'):
            url = self.path + FILE_EXT
        else:
            if hasattr(self,'compound'):
                url = self.compound.full_url()
            else:
                print ("NO COMPOUND ON OBJECT WITHOUT PATH")
                dump (self)
                url = "<undefined>"

        if hasattr(self,'anchor'):
            url += "#" + self.anchor
        return url

    def full_path (self):
        global FILE_EXT
        global OUTPUT_DIR

        if hasattr(self,'path'):
            url = self.path + FILE_EXT
        else:
            if hasattr(self,'compound'):
                url = self.compound.full_url()
            else:
                print ("NO COMPOUND ON OBJECT WITHOUT PATH")
                dump (self)
                url = "<undefined>"

        return OUTPUT_DIR + "/" + url

def dump (obj):
    pprint (vars(obj))
