from doxylayout import *
from doxybase import *
import doxylayout
#import doxytiny


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

    Importer.navitems.sort(key=lambda v: v.order)

    Importer.writer.element("div", None, {"class": "navbar"})
    Importer.writer.element("div", None, {"class": "navbar-inner"})

    Importer.writer.element("a", "Sample Docs", {"href": "#", "class": "brand"})

    Importer.writer.element("ul", None, {"class": "nav"})

    for item in Importer.navitems:
        Importer.writer.element("li")
        Importer.writer.element("a", item.label, {"href": item.ref.full_url()})
        Importer.writer.element("/li")

    Importer.trigger("navheader")

    Importer.writer.element("/ul")

    Importer.writer.element("/div")
    Importer.writer.element("/div")

def member_list_protection(member):

    if member.protection is not None:
        labelStyle = ""
        if member.protection == "public":
            labelStyle = "label-success"
        elif member.protection == "private":
            labelStyle = "label-inverse"
        elif member.protection == "protected":
            labelStyle = "label-warning"
        elif member.protection == "package":
            labelStyle = "label-info"

        Importer.writer.element("span", member.protection.title(), {"class": "label " + labelStyle})

    if member.readonly:
        Importer.writer.element("span", "Readonly", {"class": "label label-warning"})
    if member.static:
        Importer.writer.element("span", "Static", {"class": "label label-info"})

def member(m):

    #member_list_protection(m)


    doxylayout._base_member(m)

def member_heading(m):

    Importer.writer.element("div", None, {"class": "member-side-prot"})
    if m.protection is not None:
        labelStyle = ""
        if m.protection == "public":
            labelStyle = "label-success"
        elif m.protection == "private":
            labelStyle = "label-inverse"
        elif m.protection == "protected":
            labelStyle = "label-warning"
        elif m.protection == "package":
            labelStyle = "label-info"

        Importer.writer.element("span", m.protection.title(), {"class": "label " + labelStyle})

    if m.readonly:
        Importer.writer.element("span", "Readonly", {"class": "label label-warning"})
    if m.static:
        Importer.writer.element("span", "Static", {"class": "label label-info"})

    Importer.writer.element("/div")

    #Note, slightly unsafe, could possibly break html
    Importer.writer.element("h3", None, {"id": m.anchor})

    type = m.type
    if type is not None:

        #Write type
        linked_text(type)

    Importer.writer += " "

    Importer.writer.element("/span")
    Importer.writer.element("span", None, {"class": 'member-name'})

    name = m.name
    #Importer.writer.element("b",name)
    Importer.writer += name

    #These kinds of members have a () list
    if m.kind == "function":
        Importer.writer += " "

        Importer.writer.element("span", None, {"class": "member-params"})
        Importer.writer += "("
        for i, param in enumerate(m.params):
            Importer.writer += " "

            # Print the type of the parameter. Will also do some checking to add external types
            linked_text(param.type)

            Importer.writer += " "

            if param.description is not None:
                Importer.pushwriter()
                description(param.description)
                tooltip = Importer.popwriter()
                Importer.writer.element("span", None, {"data-original-title": tooltip})
                Importer.writer += param.name
                Importer.writer.element("/span")
            else:
                Importer.writer += param.name

            if i < len(m.params) - 1:
                Importer.writer += ","

        Importer.writer += ")"
        Importer.writer.element("/span")



    Importer.writer.element("/h3")
