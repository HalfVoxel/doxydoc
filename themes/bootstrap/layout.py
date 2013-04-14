from doxylayout import *
from doxybase import *
#import doxytiny

def begin_content():
    DocState.writer.html("<div class='span12'>")

def end_content():
    DocState.writer.html("</div>")

def navheader():
#     <div class="navbar">
#   <div class="navbar-inner">
#     <a class="brand" href="#">Title</a>
#     <ul class="nav">
#       <li class="active"><a href="#">Home</a></li>
#       <li><a href="#">Link</a></li>
#       <li><a href="#">Link</a></li>
#     </ul>
#   </div>
# </div>

    DocState.navitems.sort(key=lambda v: v.order)

    DocState.writer.element("div", None, {"class": "navbar"})
    DocState.writer.element("div", None, {"class": "navbar-inner"})

    DocState.writer.element("a", "Sample Docs", {"href": "#", "class": "brand"})

    DocState.writer.element("ul", None, {"class": "nav"})

    for item in DocState.navitems:
        DocState.writer.element("li")
        DocState.writer.element("a", item.label, {"href": item.ref.full_url()})
        DocState.writer.element("/li")
    
    DocState.writer.element("/ul")

    DocState.writer.element("/div")
    DocState.writer.element("/div")

def member_heading(m):
    #Note, slightly unsafe, could possibly break html
    DocState.writer.element("h3", None, {"id": m.anchor})

    type = m.type
    if type is not None:

        #Write type
        linked_text(type)

    DocState.writer += " "
    
    DocState.writer.element("/span")
    DocState.writer.element("span", None, {"class": 'member-name'})

    name = m.name
    #DocState.writer.element("b",name)
    DocState.writer += name

    if m.params is not None:
        DocState.writer += " "

        DocState.writer.element("span", None, {"class": "member-params"})
        DocState.writer += "("
        for i, param in enumerate(m.params):
            DocState.writer += " "
            markup(param.type)

            DocState.writer += " "

            if param.description is not None:
                DocState.pushwriter()
                description(param.description)
                tooltip = DocState.popwriter()
                DocState.writer.element("span", None, {"data-original-title": tooltip})
                DocState.writer += param.name
                DocState.writer.element("/span")
            else:
                DocState.writer += param.name
            
            if i < len(m.params) - 1:
                DocState.writer += ","

        DocState.writer += ")"
        DocState.writer.element("/span")



    DocState.writer.element("/h3")

    if m.protection is not None:
        labelStyle = ""
        if m.protection is "public":
            labelStyle = "label-success"
        elif m.protection is "private":
            labelStyle = "label-inverse"
        elif m.protection is "protected":
            labelStyle = "label-warning"
        elif m.protection is "package":
            labelStyle = "label-info"

        DocState.writer.element("span", m.protection.title(), {"class": "label " + labelStyle})

    if m.readonly:
        DocState.writer.element("span", "Readonly", {"class": "label label-warning"})
    if m.static:
        DocState.writer.element("span", "Static", {"class": "label label-info"})
