import types
from xml.sax.saxutils import escape
from typing import Any, Dict, Union, List


# escape() and unescape() takes care of &, < and >.
html_escape_table = {
    '"': "&quot;",
    "'": "&apos;"
}
html_unescape_table = {v: k for k, v in html_escape_table.items()}


def paramescape(v: str) -> str:
    return escape(v, html_escape_table)


class Reverter():
    def __init__(self, buffer: 'StrTree', tag: str) -> None:
        self.buffer = buffer
        self.tag = tag

    def __enter__(self) -> None:
        if self.tag is not None:
            self.buffer.close(self.tag)

    def __exit__(self, type, value, traceback) -> None:
        if self.tag is not None:
            self.buffer.open(self.tag)


class StrTree:
    """ Efficient string concatenation and some helper methods for dealing with HTML """

    def __init__(self, initial_contents=None, escape_html=True) -> None:
        self.contents = []  # type: List[Union[str, StrTree]]
        self.elementStack = []  # type: List[str]
        self.escape_html = escape_html
        if initial_contents is not None:
            self.append(initial_contents)

    def append(self, s: Union[str, 'StrTree']) -> 'StrTree':
        assert s is not None
        if isinstance(s, str):
            self.contents.append(escape(s) if self.escape_html else s)
        else:
            self.contents.append(s)
        return self

    def html(self, s: Union[str, 'StrTree']) -> 'StrTree':
        assert s is not None
        self.contents.append(s)
        return self

    def outside_paragraph(self) -> Reverter:
        return Reverter(self, "p")

    def element(self, t: str, contents: Union[types.FunctionType, str]=None, params: Dict[str, str]=None) -> 'StrTree':
        assert t is not None
        assert contents is not None
        self.open(t, params)

        if isinstance(contents, types.FunctionType):
            # Assumed to do some string tree stuff
            contents()
        else:
            self.append(contents)

        self.close(t)
        return self

    def voidelem(self, t: str) -> 'StrTree':
        self.open(t)
        self.elementStack.pop()
        return self

    def elem(self, t: str) -> 'StrTree':
        assert t is not None
        self.contents.append("<")
        self.contents.append(t)
        self.contents.append(">")
        return self

    def open(self, t: str, params: Dict[str, str]=None) -> 'StrTree':
        assert t is not None
        self.contents.append("<")
        self.contents.append(t)
        if params is not None:
            self.contents.append(" ")
            for k, v in params.items():
                if v is not None:
                    sv = str(v)
                    if len(sv) > 0:
                        self.contents.append(k + "='" + paramescape(sv) + "' ")

        self.contents.append(">")
        self.elementStack.append(t)
        return self

    def close(self, t: str) -> 'StrTree':
        assert t is not None
        if len(self.elementStack) == 0:
            raise Exception("Tried to close element, but no elements have been opened")
        elif self.elementStack[-1] != t:
            raise Exception("Tried to close '%s', but the top element was '%s'" % (t, self.elementStack[-1]))
        self.elementStack.pop()
        self.contents.append("</")
        self.contents.append(t)
        self.contents.append(">")
        return self

    def _gather(self, into: Union['StrTree', List[str]]) -> None:
        for s in self.contents:
            if isinstance(s, StrTree):
                s._gather(into)
            else:
                into.append(s)

    def __str__(self) -> str:
        res = []  # type: List[str]
        self._gather(res)
        return "".join(res)

    def __add__(self, other: Any) -> 'StrTree':
        return StrTree(escape_html=self.escape_html).append(self).append(other)

    def __iadd__(self, other: Any) -> 'StrTree':
        return self.append(other)
