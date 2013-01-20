from pprint import pprint

FILE_EXT = ".html"

class DocObj:
    
    def full_url (self):
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

def dump (obj):
    pprint (vars(obj))
