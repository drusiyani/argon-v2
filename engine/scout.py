"""The research scout. Every Friday:
  1. SCOUT (Claude Haiku) reads new research: arXiv trading papers, GitHub strategy projects, and anything Dru drops
     into vault/Ideas/Inbox.md. It picks the ideas that could work on intraday US index futures.
  2. RECIPE BUILDER (Claude Sonnet) turns the best ideas into recipes, built only from the engine's fixed menu.
  3. CRITIC: automatic checks first (engine/recipes.py: no peeking, at most 12 settings, costs on), then the recipe is
     tested on 5 years of real futures, then Claude Sonnet reviews the result in plain English.
Everything lands in data/scout.json, which feeds the site's Lab tab and the brain's Ideas/Scout notes.
"""
import os,sys,json,re,time,urllib.request,urllib.parse,datetime as dt,xml.etree.ElementTree as ET
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.join(ROOT,'engine'))
import recipes
KEY=os.environ.get('ANTHROPIC_API_KEY'); FAST=os.environ.get('ARGON_AGENT_MODEL','claude-haiku-5-5'); SMART=os.environ.get('ARGON_CHIEF_MODEL','claude-sonnet-5-5')
OUT=os.path.join(ROOT,'data','scout.json'); SEEN=os.path.join(ROOT,'data','scout_seen.json')
def ask(model,system,user,max_tokens=900):
    body=json.dumps({'model':model,'max_tokens':max_tokens,'system':system,'messages':[{'role':'user','content':user}]}).encode()
    req=urllib.request.Request('https://api.anthropic.com/v1/messages',data=body,headers={'x-api-key':KEY,'anthropic-version':'2023-06-01','content-type':'application/json'})
    t=json.loads(urllib.request.urlopen(req,timeout=120).read())['content'][0]['text']
    try: return json.loads(t[t.index('{'):t.rindex('}')+1])
    except Exception: return {'error':t[:300]}
def get(url,headers=None):
    req=urllib.request.Request(url,headers=dict({'User-Agent':'argon-v2-scout'},**(headers or {})))
    return urllib.request.urlopen(req,timeout=40).read()
def sources():
    items=[]
    try:   # arXiv: newest papers on trading, filtered to intraday / futures / index topics
        q=urllib.parse.quote('cat:q-fin.TR AND (abs:intraday OR abs:futures OR abs:"index")')
        x=ET.fromstring(get(f'http://export.arxiv.org/api/query?search_query={q}&sortBy=submittedDate&sortOrder=descending&max_results=15'))
        ns={'a':'http://www.w3.org/2005/Atom'}
        for e in x.findall('a:entry',ns):
            items.append(dict(kind='paper',title=' '.join(e.find('a:title',ns).text.split()),url=e.find('a:id',ns).text,text=' '.join(e.find('a:summary',ns).text.split())[:1500]))
    except Exception as ex: print('arXiv skipped:',ex)
    try:   # GitHub: recently updated strategy projects
        h={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN']} if os.environ.get('GITHUB_TOKEN') else {}
        r=json.loads(get('https://api.github.com/search/repositories?q='+urllib.parse.quote('intraday futures strategy backtest')+'&sort=updated&per_page=10',h))
        for g in r.get('items',[]):
            txt=g.get('description') or ''
            try: txt+=' '+get(f"https://raw.githubusercontent.com/{g['full_name']}/{g['default_branch']}/README.md").decode('utf-8','ignore')[:1500]
            except Exception: pass
            items.append(dict(kind='github',title=g['full_name'],url=g['html_url'],text=' '.join(txt.split())[:1500]))
    except Exception as ex: print('GitHub skipped:',ex)
    inbox=os.path.join(ROOT,'vault','Ideas','Inbox.md')
    if os.path.exists(inbox):   # Dru's own ideas: any bullet under the "my notes" line
        body=open(inbox).read().split('%% my notes below',1)[-1]
        for line in body.splitlines():
            if line.strip().startswith('- ') and len(line.strip())>8: items.append(dict(kind='dru',title=line.strip()[2:80],url='vault/Ideas/Inbox.md',text=line.strip()[2:]))
    return items
MENU_TEXT="""Recipe menu (use ONLY these; lists of values are the settings to try, at most 12 combinations in total):
signal: {"type":"range_breakout","minutes":[5,15,30]}  enter when price closes outside the first N minutes' range
        {"type":"gap","mode":"fade"|"follow","min_gap_atr":[0.1,0.3]}  trade the gap between yesterday's close and today's open
        {"type":"prior_day_break","mode":"follow"|"fade"}  price closes beyond yesterday's high or low
        {"type":"time_momentum","at":["10:00","10:30"],"mode":"follow"|"fade"}  direction of the move from the open by a time
        {"type":"stretch_fade","sigma":[1.0,1.5]}  fade a move from the open bigger than k x its usual size
filters (optional list): "trend20" (only with the 20-day trend), "skip_monday", "skip_friday", "calm_days", "busy_days"
stop: {"type":"atr","frac":[0.15,0.3]} (fraction of a normal day's range) or {"type":"range"} (only with range_breakout)
exit: {"type":"R","mult":[1,2,3]} (target as a multiple of the risk) or {"type":"close"} (hold to 15:59)
markets: any of ["NQ","ES","YM","RTY"]. Sessions are 09:30-16:00 New York; entries stop at 15:00."""
def run(max_ideas=2):
    if not KEY: print('No ANTHROPIC_API_KEY: the scout stays home this week.'); return
    seen=set(json.load(open(SEEN))) if os.path.exists(SEEN) else set()
    fresh=[s for s in sources() if s['url'] not in seen][:14]
    print('new sources:',len(fresh))
    rated=[]
    for s in fresh:
        r=ask(FAST,"You are the Scout on Argon's research desk. Argon paper-trades intraday US index futures (Nasdaq, S&P 500, Dow, Russell 2000), one session at a time, no overnight holds. Reply with JSON only.",
              f"Source ({s['kind']}): {s['title']}\n{s['text']}\n\nIn plain English: what is the trading idea, if any? Could it work intraday on US index futures, and could it plausibly be tested with simple rules? "
              'Reply {"idea":"one or two sentences, or empty if there is no trading idea","fit":0-10,"why":"one sentence"}',300)
        seen.add(s['url'])
        if r.get('idea') and isinstance(r.get('fit'),(int,float)): rated.append((r['fit'],s,r))
    rated.sort(key=lambda x:-x[0])
    found=json.load(open(OUT)) if os.path.exists(OUT) else {'ideas':[]}
    for fit,s,r in rated[:max_ideas]:
        if fit<5: break
        recipe=ask(SMART,"You are the Recipe Builder on Argon's research desk. You turn a trading idea into a recipe the test engine can run. Only use the menu. Be faithful to the idea; if it can't be expressed with the menu, say so. Reply with JSON only.",
                   f"Idea: {r['idea']}\nSource: {s['title']} ({s['url']})\n\n{MENU_TEXT}\n\nReply with "
                   '{"name":"short name","idea":"one sentence","markets":[...],"signal":{...},"filters":[...],"stop":{...},"exit":{...}} '
                   'or {"cannot":"why it cannot be built from the menu"}',700)
        card=dict(date=dt.date.today().isoformat(),source=dict(kind=s['kind'],title=s['title'],url=s['url']),idea=r['idea'],fit=fit,why=r.get('why'))
        if recipe.get('cannot') or recipe.get('error'):
            card.update(verdict="couldn't be built from the menu",note=recipe.get('cannot') or recipe.get('error')); found['ideas'].append(card); continue
        probs=recipes.critic_static(recipe)
        if probs:   # one chance to fix it
            recipe=ask(SMART,"You are the Recipe Builder. The critic rejected your recipe. Fix it using only the menu. Reply with the corrected recipe JSON only.",f"Recipe: {json.dumps(recipe)}\nProblems: {probs}\n\n{MENU_TEXT}",700)
        recipe['source']=s['url']; res=recipes.test(recipe); curve=res.pop('curve',None)
        review={}
        if 'summary' in res:
            review=ask(SMART,"You are the Critic on Argon's research desk. You are sceptical and fair. You look for overfitting, luck, results that only worked in one period, and results no better than random. Use only the numbers given; do not invent any. Reply with JSON only.",
                       f"Recipe: {json.dumps(recipe)}\nTest on 5 years of real futures (settings re-picked monthly, costs included): {json.dumps(res)}\n\n"
                       'Reply {"review":"two or three plain sentences a 16-year-old could follow","keep":true|false}',400)
        card.update(recipe=recipe,result=res,curve=curve,review=review.get('review'),keep=review.get('keep'),verdict=res.get('verdict'))
        found['ideas'].append(card); print(card['recipe'].get('name'),'->',card['verdict'])
    found['ideas']=found['ideas'][-60:]; found['updated']=dt.datetime.utcnow().strftime('%Y-%m-%d %H:%MZ')
    json.dump(found,open(OUT,'w'),indent=1); json.dump(sorted(seen),open(SEEN,'w'))
def seed():
    """Fills data/scout.json with the three seed examples (no AI needed), so the site shows how the scout works."""
    found={'ideas':[],'seed':True}
    for r in [dict(name='Gap fade',idea='Big overnight gaps tend to partly close in the first hours.',markets=['NQ','ES','YM','RTY'],signal=dict(type='gap',mode='fade',min_gap_atr=[0.15,0.3]),filters=[],stop=dict(type='atr',frac=[0.15,0.3]),exit=dict(type='R',mult=[1,2])),
              dict(name='Ten-o-clock momentum',idea='The first 30 minutes set the tone: follow the move from the open at 10:00.',markets=['NQ','ES','YM','RTY'],signal=dict(type='time_momentum',at=['10:00','10:30'],mode='follow'),filters=['trend20'],stop=dict(type='atr',frac=[0.15,0.3]),exit=dict(type='close')),
              dict(name='Over-tuned breakout',idea='A deliberately over-tuned recipe, to show the critic stopping it.',markets=['NQ'],signal=dict(type='range_breakout',minutes=[5,10,15,30]),filters=[],stop=dict(type='atr',frac=[0.1,0.2,0.3]),exit=dict(type='R',mult=[1,2,3]))]:
        res=recipes.test(r); curve=res.pop('curve',None)
        found['ideas'].append(dict(date=dt.date.today().isoformat(),source=dict(kind='example',title='seed example',url=''),idea=r['idea'],recipe=r,result=res,curve=curve,verdict=res.get('verdict'),seed=True))
    found['updated']=dt.datetime.utcnow().strftime('%Y-%m-%d %H:%MZ'); json.dump(found,open(OUT,'w'),indent=1); print('seed examples written')
if __name__=='__main__':
    seed() if 'seed' in sys.argv else run()
