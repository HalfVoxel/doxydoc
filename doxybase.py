from pprint import pprint

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

class StringBuilder:

    def __init__ (self):
        self.arr = []
        self.cache = ""

    def __add__ (self, t):
        assert t
        self.arr.append (t)
        return self

    def __iadd__ (self, t):
        assert t
        self.arr.append (t)
        return self

    def __str__ (self):
        self.cache = ''.join(self.arr)
        del self.arr[:]
        self.arr.append(self.cache)
        return self.cache

    def clear (self):
        del self.arr[:]

class DocState:
    writer = StringBuilder()
    compound = None

class DocSettings:
    header = "<html>"
    footer = "</html>"
    external = {}

class DocObj:
    
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
