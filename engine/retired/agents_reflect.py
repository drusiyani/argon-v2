"""Weekly: each agent reads its own calls and what happened, and rewrites its own lessons. This is how each brain grows."""
import os,json,urllib.request
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); MEM=os.path.join(ROOT,'data','agent_memory')
KEY=os.environ.get('ANTHROPIC_API_KEY'); MODEL=os.environ.get('ARGON_AGENT_MODEL','claude-haiku-5-5')
if not KEY: raise SystemExit('no key')
farm=json.load(open(os.path.join(ROOT,'data','farm.json'))); out={t['key']:t['R'] for t in farm['trades'] if t.get('route')=='feed'}
for fn in os.listdir(MEM):
    name=fn[:-5]; m=json.load(open(os.path.join(MEM,fn)))
    for c in m['calls']: c['R']=out.get(c['key'],c.get('R'))
    done=[c for c in m['calls'] if c.get('R') is not None][-40:]
    if not done: continue
    log='\n'.join(f"- {c['when']} {c['setup']}: said {c['view']} ({c['confidence']}%), result {c['R']:+.2f}R" for c in done)
    prompt=(f"You are {name} on Argon's paper-trading desk. Here are your recent calls and what each setup actually made (R = times the risk; positive means taking it was right).\n{log}\n\n"
            f"Your current lessons: {m['lessons']}\n\nRewrite your lessons: at most 8 short, specific bullets about what you should do differently, based only on this evidence. Keep lessons that still hold, drop ones the results contradict. Reply with JSON only: {{\"lessons\":[...]}}")
    body=json.dumps({'model':(os.environ.get('ARGON_CHIEF_MODEL','claude-sonnet-5-5') if name=='Chief' else MODEL),'max_tokens':500,'messages':[{'role':'user','content':prompt}]}).encode()
    req=urllib.request.Request('https://api.anthropic.com/v1/messages',data=body,headers={'x-api-key':KEY,'anthropic-version':'2023-06-01','content-type':'application/json'})
    t=json.loads(urllib.request.urlopen(req,timeout=90).read())['content'][0]['text']
    try: m['lessons']=json.loads(t[t.index('{'):t.rindex('}')+1])['lessons'][:8]
    except Exception: pass
    json.dump(m,open(os.path.join(MEM,fn),'w'),indent=1); print(name,'lessons:',len(m['lessons']))
