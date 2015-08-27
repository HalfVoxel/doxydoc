from pprint import pprint


class EntityPath:
    def __init__(self):
        self.path = None
        self.anchor = None
        self.parent = None
        self.page = None

    def full_url(self):
        ''' Url to the page (including possible anchor) where the Entity exists '''

        url = self.page_url()
        if self.anchor is not None:
            url += "#" + self.anchor
        return url

    def page_url(self):
        ''' Url to the page where the Entity exists '''

        if hasattr(self, 'exturl'):
            return self.exturl

        if self.path is not None:
            url = self.path
        else:
            if self.parent is not None:
                url = self.parent.page_url()
            else:
                url = "<undefined>"

        return url

    def full_path(self):
        ''' Path to the file which contains this Entity '''

        if self.path is not None:
            url = self.path
        else:
            if self.parent is not None:
                url = self.parent.full_url()
            else:
                url = "<undefined>"

        return "todo" + "/" + url


def dump(obj):
    pprint(vars(obj))
