"""The desk: four AI agents, each with its own brain, judging every setup the rules flag, live and forward only.

Why forward only: an AI model has read about the past, so testing it on old prices is quietly cheating.
Every call is logged with what each agent could see at the time, then scored against what actually happened.
Needs ANTHROPIC_API_KEY. Run every 15 minutes during the London and New York sessions (the workflow does this).
"""
import os,sys,json,time,urllib.request,datetime as dt
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY=os.environ.get('ANTHROPIC_API_KEY'); MODEL=os.environ.get('ARGON_AGENT_MODEL','claude-haiku-5-5'); CHIEF_MODEL=os.environ.get('ARGON_CHIEF_MODEL','claude-sonnet-5-5')   # the Chief gets the stronger brain
CALLS=os.path.join(ROOT,'data','desk_calls.jsonl'); MEM=os.path.join(ROOT,'data','agent_memory'); os.makedirs(MEM,exist_ok=True)
AGENTS={
 'Scout':{'mark':'scout','job':"You hunt for the strongest version of each setup. Judge the quality of the level that was swept, how cleanly price snapped back, and how decisive the trend flip was. Count it in the setup's favour when the other strategies or Kronos point the same way. Argue for taking setups that look genuinely good, and say so plainly when they don't."},
 'Sceptic':{'mark':'sceptic','job':"Your job is to find the reason this trade fails: a choppy day, news time (8:30am New York), a weak or already-used level, trading against the hourly trend, a small reward, a sweep that took too long to come back, or the other strategies and Kronos pointing the opposite way. You are allowed to like a setup, but only after trying hard to break it."},
 'Risk':{'mark':'risk','job':"You protect the account. Look at today's results so far, losing streaks, and every trade already open across ALL of Argon's strategies, not just the desk (the four markets usually move together, so an opening-range long on the Nasdaq plus a desk long on the S&P is really one big bet). Check the reward is worth the risk. Say skip when the account would be exposed."},
}
CHIEF={'mark':'chief','job':"You run the desk. Read the Scout, the Sceptic and Risk, the other strategies' positions and Kronos's forecast, check your own past decisions and lessons, then decide take or skip. You are scored on one thing: whether the setups you take beat simply taking every setup."}
def ask(system,user,max_tokens=350,model=None):
    body=json.dumps({'model':model or MODEL,'max_tokens':max_tokens,'system':system,'messages':[{'role':'user','content':user}]}).encode()
    req=urllib.request.Request('https://api.anthropic.com/v1/messages',data=body,headers={'x-api-key':KEY,'anthropic-version':'2023-06-01','content-type':'application/json'})
    t=json.loads(urllib.request.urlopen(req,timeout=90).read())['content'][0]['text']
    try: return json.loads(t[t.index('{'):t.rindex('}')+1])
    except Exception: return {'view':'skip','confidence':0,'reason':'could not read my own answer: '+t[:120]}
def memory(name):
    p=os.path.join(MEM,name+'.json'); return json.load(open(p)) if os.path.exists(p) else {'lessons':[],'calls':[]}
def save_memory(name,m): json.dump(m,open(os.path.join(MEM,name+'.json'),'w'),indent=1)
def mistake_text():
    p=os.path.join(ROOT,'data','mistakes.json')
    if not os.path.exists(p): return ''
    M=json.load(open(p)); worst=[b for b in M['book'] if b['avg_with']<b['avg_without']][:4]
    return ("\n\nTHE DESK'S MISTAKE BOOK (learned from every losing setup since 2024):\n"+'\n'.join(f"- {b['label']}: {b['avg_with']:+.2f}R a trade when it happens vs {b['avg_without']:+.2f}R when it doesn't ({b['n']} examples)" for b in worst)
            +("\nAvoid this month: "+', '.join(M['tags'][k] for k in M['now']) if M['now'] else ''))
def brain_text(name):
    m=memory(name); past=m['calls'][-15:]
    lines=[f"- {c['when']} {c['setup']}: you said {c['view']} ({c['confidence']}%), outcome {c.get('R','pending')}" for c in past]
    return "YOUR LESSONS SO FAR:\n"+('\n'.join('- '+l for l in m['lessons']) or '- none yet')+"\n\nYOUR RECENT CALLS:\n"+('\n'.join(lines) or '- none yet')+mistake_text()
FORMAT='Reply with JSON only: {"view":"take" or "skip","confidence":0-100,"reason":"one or two plain sentences"}'
def judge(setup_text,desk_state):
    views={}
    for name,a in AGENTS.items():
        system=f"You are {name}, one of four AI agents on Argon's paper-trading desk (US index futures: Nasdaq, S&P 500, Dow, Russell 2000). {a['job']} You only know what is written below; nothing after this moment. {FORMAT}"
        views[name]=ask(system,f"{brain_text(name)}\n\nTHE DESK TODAY:\n{desk_state}\n\nTHE SETUP:\n{setup_text}")
    others='\n'.join(f"{n}: {v.get('view')} ({v.get('confidence')}%): {v.get('reason')}" for n,v in views.items())
    system=f"You are the Chief of Argon's paper-trading desk. {CHIEF['job']} {FORMAT.replace('view','decision')}"
    chief=ask(system,model=CHIEF_MODEL,user=f"{brain_text('Chief')}\n\nTHE DESK TODAY:\n{desk_state}\n\nTHE SETUP:\n{setup_text}\n\nYOUR AGENTS SAY:\n{others}")
    return views,chief
KRONOS_URL=os.environ.get('KRONOS_URL')   # a JSON file Argon v1 publishes: {"NQ":{"direction":"up","confidence":0.62,"horizon":"1h","updated":"..."},...}
def kronos():
    p=os.path.join(ROOT,'data','kronos.json')
    if os.path.exists(p):
        try: return json.load(open(p))     # Argon v2's own Kronos-small
        except Exception: pass
    if not KRONOS_URL: return None
    try: return json.loads(urllib.request.urlopen(KRONOS_URL,timeout=20).read())
    except Exception: return None
def others_text(c,trades,kr):
    """What the rest of Argon is saying at the moment of this setup: no peeking at anything after it."""
    t=c['m']['t']+300; d=c['sd']; s=c['s']; lines=[]
    orb=[x for x in trades if x.get('route')=='orb' and x['inst']==s and x['sd']==d and x['fill_t']<=t]
    if orb: x=orb[0]; lines.append(f"Opening-range strategy on {PN[s]} today: {'bought' if x['side']=='long' else 'sold'} at {x['entry']:,.2f}"+(' and is still in the trade.' if x['exit_t']>t else ' and has already closed.'))
    else: lines.append(f"Opening-range strategy on {PN[s]} today: no trade yet.")
    openx=[x for x in trades if x.get('route') in ('ob','orb','chain') and x.get('fired') and x.get('fill_t') and x['fill_t']<=t<x.get('exit_t',0)]
    lines.append('Trades open right now across all strategies: '+(', '.join(f"{x['route'].replace('ob','order-block').replace('chain','main')} {'long' if x['side']=='long' else 'short'} {PN[x['inst']]}" for x in openx) or 'none')+'.')
    strict=[x for x in trades if x.get('route')=='chain' and x['inst']==s and x['sweep_t']==c['sw']['t']]
    lines.append('The strict main strategy '+('would also take this setup.' if strict and strict[0].get('fired') else 'would NOT take this setup (it is stricter).'))
    k=(kr or {}).get(s)
    lines.append(f"Kronos forecast for {PN[s]}: {k['direction']} ({round(100*k.get('confidence',0))}% confident, next {k.get('horizon','?')})." if k else 'Kronos forecast: not available.')
    return '\n'.join(lines)
def setup_text(c,sm,bars_today):
    sw=c['sw']; p=c['p']; tnow=dt.datetime.fromtimestamp(c['m']['t']+300,NY)
    rng=max(b['h'] for b in bars_today)-min(b['l'] for b in bars_today) if bars_today else 0
    return (f"Market: {PN[c['s']]} futures. Time: {tnow:%A %d %b %H:%M} New York.\n"
            f"Level: {lvl_name(p)} at {p['p']:,.2f}. Price poked past it and {('came straight back' if sw['cls']=='manipulation' else 'came back within 10 minutes')}.\n"
            f"Other market ({PN.get(sw['pair']['pair'],'?') if sw['pair'] else '?'}): {'did NOT follow (SMT)' if sw['smt'] else 'followed too'}.\n"
            f"Trend flipped with a big candle at {dt.datetime.fromtimestamp(c['m']['t'],NY):%H:%M}. Hourly trend: {'agrees' if c['h1'] else 'disagrees'} with this trade.\n"
            f"Plan: {'BUY' if c['side']=='long' else 'SELL'} at {sm['entry']:,.2f}, stop {sm['stop']:,.2f}, target {sm['target']:,.2f} ({sm['rr']:.1f}x the risk). Today's range so far: {rng:,.1f} points.")
if __name__=='__main__':
    if not KEY: print('No ANTHROPIC_API_KEY, the desk stays closed.'); sys.exit(0)
    os.environ['FARM_LIGHT']='1'
    g={'__file__':os.path.join(ROOT,'engine','farm.py'),'__name__':'farm'}
    exec(open(os.path.join(ROOT,'engine','farm.py')).read(),g)
    for k in ('CANDS','BARS','SESS_IDX','NY','PN','lvl_name','pick_sim','FEED_RULES'): globals()[k]=g[k]
    seen=set()
    if os.path.exists(CALLS):
        for line in open(CALLS):
            try: seen.add(json.loads(line)['key'])
            except Exception: pass
    KR=kronos()
    now=time.time(); today=[json.loads(l) for l in open(CALLS)] if os.path.exists(CALLS) else []
    tday=dt.datetime.now(NY).date().isoformat(); taken=[d for d in today if d.get('day')==tday and d['chief'].get('decision')=='take']
    for c in CANDS:
        if not (c['m'] and c['m']['disp'] and c['st']['2'][0]): continue
        if now-(c['m']['t']+300)>1800 or now<c['m']['t']+300: continue      # only fresh setups: the decision happens before anyone knows the result
        key=f"{c['s']}-{c['sw']['t']}"
        if key in seen: continue
        sm=pick_sim(c,FEED_RULES)
        if not sm: continue
        idx=SESS_IDX[c['s']][c['sw']['sd']]; bars_today=[BARS[c['s']]['5m'][i] for i in idx if BARS[c['s']]['5m'][i]['t']<=c['m']['t']]
        state=f"Setups the desk has taken today: {len(taken)}. Markets with an open idea: {', '.join(sorted(set(d['inst'] for d in taken))) or 'none'}."
        views,chief=judge(setup_text(c,sm,bars_today)+"\n\nWHAT THE REST OF ARGON IS SAYING:\n"+others_text(c,g['TRADES'],KR),state)
        rec=dict(key=key,day=tday,inst=c['s'],when=dt.datetime.fromtimestamp(c['m']['t']+300,NY).strftime('%Y-%m-%d %H:%M'),setup=f"{'buy' if c['side']=='long' else 'sell'} {PN[c['s']]} after {lvl_name(c['p'])}",views=views,chief=chief,model=MODEL,chief_model=CHIEF_MODEL)
        open(CALLS,'a').write(json.dumps(rec)+'\n'); seen.add(key)
        for name,v in list(views.items())+[('Chief',{'view':chief.get('decision'),'confidence':chief.get('confidence'),'reason':chief.get('reason')})]:
            m=memory(name); m['calls'].append(dict(key=key,when=rec['when'],setup=rec['setup'],view=v.get('view'),confidence=v.get('confidence'))); save_memory(name,m)
        print('desk:',rec['setup'],'->',chief.get('decision'))
