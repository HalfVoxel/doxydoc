import urllib2
import re

def main ():

    urlbase = "http://docs.unity3d.com/Documentation/ScriptReference/"

    f = urllib2.urlopen (urlbase + "20_class_hierarchy.html")
    text = f.read ()

    flist = open ("external.csv", "w")
    for match in re.finditer ("<a\s+href=\"([^\"]*)\"\s+class=\"classlink\"\s*>(.*?)</a>", text):
        flist.write (match.group(2) + ", " + urlbase + match.group(1) + "\n")

    flist.close()

main ()