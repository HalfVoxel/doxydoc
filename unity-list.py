import urllib3
import re


def main():
    urlbase = "https://docs.unity3d.com/ScriptReference/"
    http = urllib3.PoolManager()
    text = http.request('GET', urlbase + "docdata/toc.js").data.decode('utf-8')

    flist = open("external.csv", "w")
    # for match in re.finditer("<a\s+href=\"([^\"]*)\"\s+class=\"classlink\"\s*>(.*?)</a>", text):
    for match in re.finditer('"link":"(.+?)"', text):
        if match.group(1) != "null":
            flist.write(match.group(1) + ", " + urlbase + match.group(1) + ".html\n")

    flist.close()


main()
