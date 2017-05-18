#!/bin/bash

# python3 doxydoc.py
cd html
s='s#<a href=(['\''"])[^"'\'':]+['\''"][^>]*?>(.*?)</a>#<a href=\1http://arongranberg.com/astar/docs\1>\2</a>#g';
banner="<div class='alert alert-danger' role='alert'>This is an excerpt from the full documentation. You can view the full documentation <a href='http://arongranberg.com/astar/docs'>here</a>. Most links on this page will just take you to the full documentation.</div>"

for file in *.html; do
	cat $file | sed -E "s#<script src='(https://cdn.jsdelivr.net/fuse/2.5.0/fuse.min.js|resources/js/elasticlunr.js)'></script>##g" | html-inline | perl -pe "$s" | perl -pe "s#(</h1>)#\1$banner#" | perl -pe "s#(Good Luck! </p>)#\1$banner#" > '/tmp/tmp.html'
	mv '/tmp/tmp.html' $file
done
# sed -E 's#href=[\'"][^"\':]+[\'"]#href="http://arongranberg.com/astar"#g' > test.html