import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
"""Glue the page together: styles + layout + the farm's data + the app scripts -> docs/lab.html (the full dashboard; the front page is engine/build_front.py)."""
src=os.path.join(ROOT,'site','src')
d=open(os.path.join(ROOT,'data','farm.json')).read().replace('</','<\\/')
out=open(os.path.join(src,'head.html')).read()+open(os.path.join(src,'body.html')).read().replace('__DATA__',d)
for p in ['app1.js','app2.js','app3.js','app4.js','app5.js','app6.js','app7.js']: out+=open(os.path.join(src,p)).read()
pp=os.path.join(ROOT,'data','portfolio.json')
port='<script>window.PORT='+(open(pp).read().replace('</','<\\/') if os.path.exists(pp) else 'null')+';</script>\n'
out=out.replace('</body>',port+open(os.path.join(src,'app8.js')).read()+'</body>',1)
open(os.path.join(ROOT,'docs','lab.html'),'w').write(out); print('built docs/lab.html (the full dashboard)',len(out))
import runpy; runpy.run_path(os.path.join(ROOT,'engine','build_front.py'))   # the front page: docs/index.html
