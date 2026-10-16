"""Once a week Claude reads the newest parts of the brain (plus everything you've written in your notes)
and writes a short reflection that links back to what it read. Needs an ANTHROPIC_API_KEY secret; skips quietly without one."""
import os,json,re,glob,datetime as dt,urllib.request
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); V=os.path.join(ROOT,'vault')
MARK='%% my notes below. Argon never changes anything under this line %%'
key=os.environ.get('ANTHROPIC_API_KEY')
if not key: print('no API key, skipping reflection'); raise SystemExit
def read(p,n=4000): return open(p).read()[:n]
parts=[]
for name in ('Home.md','Questions/Questions.md','Rules/Lessons.md'):
    p=os.path.join(V,name)
    if os.path.exists(p): parts.append(f'### {name}\n'+read(p))
for p in sorted(glob.glob(os.path.join(V,'Lab','*.md')))[-2:]+sorted(glob.glob(os.path.join(V,'Days','*.md')))[-5:]: parts.append(f'### {os.path.basename(p)}\n'+read(p,2500))
mine=[]
for p in glob.glob(os.path.join(V,'**','*.md'),recursive=True):
    s=open(p).read()
    if MARK in s:
        t=s.split(MARK,1)[1].replace('## My notes','').strip()
        if t: mine.append(f'### Dru on [[{os.path.basename(p)[:-3]}]]\n'+t[:1500])
week=dt.date.today().isocalendar(); title=f'Reflection {week[0]}-W{week[1]:02d}'
prompt=("You are the reflective voice of a trading-research notebook called Argon. Below are its newest notes and everything its owner, Dru, "
 "has written in his own notes. Write a short reflection (under 350 words, plain English a teacher would follow) with these headings: "
 "What changed this week. What I'm more sure of. What I'm less sure of. Something to test next. Questions for Dru. "
 "Link to notes you mention using [[Note name]] exactly as the note titles appear. Be honest about small samples. No preamble.\n\n"+'\n\n'.join(parts+mine))
body=json.dumps({'model':'claude-haiku-5-5','max_tokens':1200,'messages':[{'role':'user','content':prompt}]}).encode()
req=urllib.request.Request('https://api.anthropic.com/v1/messages',data=body,headers={'x-api-key':key,'anthropic-version':'2023-06-01','content-type':'application/json'})
out=json.loads(urllib.request.urlopen(req,timeout=120).read())['content'][0]['text']
os.makedirs(os.path.join(V,'Claude'),exist_ok=True)
path=os.path.join(V,'Claude',title+'.md')
mine_part=open(path).read().split(MARK,1)[1] if os.path.exists(path) and MARK in open(path).read() else '\n## My notes\n\n'
open(path,'w').write(f"---\ntype: reflection\nweek: {week[0]}-W{week[1]:02d}\nwritten_by: Claude\n---\n# {title}\n\n{out}\n\nBack to [[Home]].\n\n{MARK}{mine_part}")
print('wrote',title)
