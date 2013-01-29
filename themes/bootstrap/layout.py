from doxylayout import *
from doxybase import *
import doxytiny

def member_heading (m):
    #Note, slightly unsafe, could possibly break html
    DocState.writer.html("<h3 id=%s>" % (m.anchor))

    type = m.type
    if type != None:

        #Write type
        linked_text(type)

    DocState.writer += " "
        
    name = m.name
    #DocState.writer.element ("b",name)
    DocState.writer += name

    DocState.writer.html("</h3>")

    if m.protection != None:
        labelStyle = ""
        if m.protection == "public":
            labelStyle = "label-success"
        elif m.protection == "private":
            labelStyle = "label-inverse"
        elif m.protection == "protected":
            labelStyle = "label-warning"
        elif m.protection == "package":
            labelStyle = "label-info"

        DocState.writer.element ("span", m.protection.title(), {"class": "label " + labelStyle})

    if m.readonly:
        DocState.writer.element ("span", "Readonly", {"class": "label label-warning"})
    if m.static:
        DocState.writer.element ("span", "Static", {"class": "label label-info"})