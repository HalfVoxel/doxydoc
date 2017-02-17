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


class StrTree:
    """ Efficient string concatenation and some helper methods for dealing with HTML """

    def __init__(self, initial_contents=None) -> None:
        self.contents = []  # type: List[Union[str, StrTree]]
        self.append(initial_contents)

    def append(self, s: Union[str, 'StrTree']) -> 'StrTree':
        if s is not None:
            if isinstance(s, str):
                self.contents.append(escape(s))
            else:
                self.contents.append(s)
        return self

    def html(self, s: Union[str, 'StrTree']) -> 'StrTree':
        assert s
        self.contents.append(s)
        return self

    def element(self, t: str, c: Any=None, params: Dict[str, str]=None) -> 'StrTree':
        assert t
        if params is None:
            self.contents.append("<" + t + ">")
        else:
            self.contents.append("<" + t + " ")
            for k, v in params.items():
                if v is not None:
                    sv = str(v)
                    if len(sv) > 0:
                        self.contents.append(k + "='" + paramescape(sv) + "' ")

            self.contents.append(">")

        if c is not None:
            if isinstance(c, types.FunctionType):
                c()
            else:
                self.append(c)

            self.contents.append("</" + t + ">")

        return self

    def elem(self, t: str) -> 'StrTree':
        assert t is not None
        self.contents.append("<")
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
        return StrTree().append(self).append(other)

    def __iadd__(self, other: Any) -> 'StrTree':
        return self.append(other)
