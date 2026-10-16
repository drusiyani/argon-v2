import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
"""Glue the page together: styles + layout + the farm's data + the app scripts -> docs/index.html (GitHub Pages)."""
src=os.path.join(ROOT,'site','src')
d=open(os.path.join(ROOT,'data','farm.json')).read().replace('</','<\\/')
out=open(os.path.join(src,'head.html')).read()+open(os.path.join(src,'body.html')).read().replace('__DATA__',d)
for p in ['app1.js','app2.js','app3.js','app4.js','app5.js','app6.js','app7.js']: out+=open(os.path.join(src,p)).read()
open(os.path.join(ROOT,'docs','index.html'),'w').write(out); print('built docs/index.html',len(out))
