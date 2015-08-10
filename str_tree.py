import types
from xml.sax.saxutils import escape

# escape() and unescape() takes care of &, < and >.
html_escape_table = {
    '"': "&quot;",
    "'": "&apos;"
}
html_unescape_table = {v: k for k, v in html_escape_table.items()}


def paramescape(v):
    return escape(v, html_escape_table)


class StrTree:
    """ Efficient string concatenation and some helper methods for dealing with HTML """

    def __init__(self, initial_contents):
        self.contents = []
        self.append(initial_contents)

    def append(self, s):
        if s is not None:
            if isinstance(s, str):
                self.contents.append(escape(s))
            else:
                self.contents.append(s)
        return self

    def html(self, s):
        self.contents.append(s)
        return self

    def element(self, t, c=None, params=None):
        assert t
        if params is None:
            self.contents.append("<" + t + ">")
        else:
            self.contents.append("<" + t + " ")
            for k, v in params:
                if v is not None and v != "":
                    self.contents.append(k + "='" + paramescape(v) + "' ")

            self.contents.append(">")

        if c is not None:
            if isinstance(c, types.FunctionType):
                self.contents.append(c())
            else:
                self.append(c)

            self.contents.append("</" + t + ">")

        return self

    def elem(self, t):
        assert t is not None
        self.contents.append("<")
        self.contents.append(t)
        self.contents.append(">")
        return self

    def _gather(self, into):
        for s in self.contents:
            if s is StrTree:
                s.gather(into)
            else:
                into.append(s)

    def __str__(self):
        res = []
        self._gather(res)
        return "".join(res)

    def __add__(self, other):
        return StrTree().append(self).append(other)

    def __iadd__(self, other):
        return self.append(other)
