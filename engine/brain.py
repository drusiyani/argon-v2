"""Argon's brain: grows the Obsidian vault every run instead of rebuilding it.

Rules it follows:
  * Never deletes a note. Days, trades, months and lab runs pile up forever.
  * Anything under the line  %% my notes below %%  belongs to you and is never touched.
  * "Living" notes (markets, levels, sessions, questions) are re-measured from all the data every run,
    and when a finding moves, the change is written into that note's history.
"""
import os,json,re,shutil,datetime as dt,collections,subprocess,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT=os.path.join(ROOT,'vault'); STATE=os.path.join(VAULT,'.argon','state.json')
MARK='%% my notes below. Argon never changes anything under this line %%'
TODAY=dt.date.today().isoformat()
os.makedirs(os.path.dirname(STATE),exist_ok=True)
state=json.load(open(STATE)) if os.path.exists(STATE) else {'facts':{},'history':{},'growth':[],'answers':{}}
written=collections.Counter(); new_notes=[]
def safe(n): return re.sub(r'[\\/:*?"<>|]','-',n)
def callouts(body):
    """Obsidian callouts instead of plain quotes (the obsidian-markdown skill's [!type] syntax)."""
    out=[];prev=''
    for line in body.split('\n'):
        if line.startswith('> ') and not prev.startswith('>') and not line.startswith('> [!'): out.append('> [!info]')
        out.append(line); prev=line
    return '\n'.join(out)
def write(folder,name,body):
    """Write the automatic part of a note; keep whatever the user wrote under the marker."""
    body=callouts(body)
    path=os.path.join(VAULT,folder,safe(name)+'.md'); os.makedirs(os.path.dirname(path),exist_ok=True)
    mine='\n## My notes\n\n'
    if os.path.exists(path):
        old=open(path).read()
        if MARK in old: mine=old.split(MARK,1)[1]
        elif '## My notes' in old: mine='\n'+old[old.index('## My notes'):]
    else: new_notes.append(name)
    open(path,'w').write(body.rstrip()+'\n\n'+MARK+mine); written[folder]+=1
def R(x): return ('+' if x>0 else '')+f'{x:.2f}R'
def pct(a,b): return f'{round(100*a/b)}%' if b else '–'
def remember(key,facts,labels):
    """Compare this run's findings with last run's and log anything that moved."""
    prev=state['facts'].get(key,{}); hist=state['history'].setdefault(key,[])
    for k,v in facts.items():
        p=prev.get(k)
        if p is None: continue
        if isinstance(v,float) and abs(v-p)>=(0.05 if abs(v)<=1.5 else 0.15*abs(p)):
            hist.append(f"{TODAY}: {labels.get(k,k)} moved from {fmtf(k,p)} to {fmtf(k,v)}")
    state['facts'][key]=facts
    return hist[-25:]
def fmtf(k,v): return f'{round(100*v)}%' if k.endswith('_rate') else R(v) if k.endswith('_R') else f'{v:.1f}'
# ---------------- 1. the site's own notes (days, trades, setups, ideas, rules, reviews)
def site_export():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError: return []
    with sync_playwright() as p:
        b=p.chromium.launch(); pg=b.new_page(); pg.goto('file://'+os.path.join(ROOT,'docs','index.html')); pg.wait_for_timeout(2500)
        files=pg.evaluate("window.__exportFiles()"); b.close(); return files
FOLD={'Daily':'Days','Concepts':'Ideas','Trades':'Trades','Setups':'Setups','Rules':'Rules','Reviews':'Reviews'}
for f in site_export():
    if '/' not in f['path']: continue
    folder,fn=f['path'].split('/',1); body=f['content']
    body=body.split('\n## My notes\n')[0]
    write(FOLD.get(folder,folder),fn[:-3],body)
# keep every rulebook version ever used
for fn in os.listdir(os.path.join(VAULT,'Rules')) if os.path.isdir(os.path.join(VAULT,'Rules')) else []:
    pass
# ---------------- 2. what the long backtest found
cd=json.load(open(os.path.join(ROOT,'data','bt_cands.json'))); C=[dict(zip(cd['cols'],r)) for r in cd['rows']]
dd=json.load(open(os.path.join(ROOT,'data','bt_days.json'))); DY=[dict(zip(dd['cols'],r)) for r in dd['rows']]
BT=json.load(open(os.path.join(ROOT,'data','bt_out.json')))
MN={'NQ':'Nasdaq','ES':'S&P 500'}; DOW=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
def level_name(c):
    n={'PDH':"Yesterday's high",'PDL':"Yesterday's low",'PWH':"Last week's high",'PWL':"Last week's low",'Asia high':'Asia high','Asia low':'Asia low','London high':'London high','London low':'London low','EQH':'Equal highs','EQL':'Equal lows'}.get(c['level'])
    return n or f"{c['level_tf']} {'highs' if c['level']=='BSL' else 'lows'}"
for c in C: c['L']=level_name(c); c['month']=c['day'][:7]
def stats(xs):
    n=len(xs); back=[x for x in xs if x['sweep']!='acceptance']; flip=[x for x in back if x['flip_big']]; tr=[x for x in xs if x['R_2R'] is not None and x['sweep']!='acceptance' and x['flip_big']]
    g=sum(x['R_2R'] for x in tr)-0.05*len(tr); w=sum(1 for x in tr if x['R_2R']>0)
    return dict(n=n,back=len(back),flip=len(flip),back_rate=len(back)/n if n else 0,flip_rate=len(flip)/len(back) if back else 0,tn=len(tr),R=g,avg_R=g/len(tr) if tr else 0,win_rate=w/len(tr) if tr else 0)
def row(label,s,link=True): return f"| {'[['+label+']]' if link else label} | {s['n']} | {pct(s['back'],s['n'])} | {pct(s['flip'],s['back'])} | {s['tn']} | {pct(round(s['win_rate']*s['tn']),s['tn'])} | {R(s['avg_R']) if s['tn'] else '–'} |"
HEAD="| | times swept | came back | then flipped | trades | won | per trade |\n|---|---|---|---|---|---|---|\n"
def what_it_means(s,thing):
    if s['tn']<30: return f"Only {s['tn']} trades so far, so nothing solid yet about {thing}."
    if s['avg_R']>0.1: return f"So far {thing} has been worth trading: {R(s['avg_R'])} a trade over {s['tn']} trades. Worth watching to see if it lasts."
    if s['avg_R']<-0.1: return f"So far {thing} has lost money: {R(s['avg_R'])} a trade over {s['tn']} trades."
    return f"So far {thing} is roughly break-even ({R(s['avg_R'])} a trade over {s['tn']} trades)."
span=f"{BT['range'][0]} to {BT['range'][1]}"
note_head=lambda kind: f"---\ntype: {kind}\nupdated: {TODAY}\nbuilt_from: {BT['sessions']} days of prices ({span})\n---\n"
LEXPLAIN="Columns: how many times price poked past it, how often it came back (a sweep, not a breakout), how often the trend then clearly flipped, and what a simple trade (enter at the order block, target 2× the risk) would have done. [[What R means]]."
# ---- markets
for s,name in MN.items():
    xs=[c for c in C if c['inst']==s]; ds=[d for d in DY if d['inst']==s]; st=stats(xs)
    avg=lambda k,a: sum(d[k] for d in a if d[k] is not None)/max(1,sum(1 for d in a if d[k] is not None))
    up=sum(1 for d in ds if d['change']>0)
    by_sess={k:stats([c for c in xs if c['session']==k]) for k in ('London','NY')}
    by_lvl=sorted(((L,stats([c for c in xs if c['L']==L])) for L in set(c['L'] for c in xs)),key=lambda x:-x[1]['n'])
    good=[x for x in by_lvl if x[1]['tn']>=30]; good.sort(key=lambda x:-x[1]['avg_R'])
    wd=[(DOW[i],avg('range',[d for d in ds if dt.date.fromisoformat(d['day']).weekday()==i])) for i in range(5)]
    facts={'ny_flip_rate':by_sess['NY']['flip_rate'],'london_flip_rate':by_sess['London']['flip_rate'],'ny_R':by_sess['NY']['avg_R'],'london_R':by_sess['London']['avg_R'],'back_rate':st['back_rate']}
    hist=remember('market:'+s,facts,{'ny_flip_rate':'New York flip rate','london_flip_rate':'London flip rate','ny_R':'New York result per trade','london_R':'London result per trade','back_rate':'came-back rate'})
    noticed=[]
    best=max(by_sess.items(),key=lambda x:x[1]['avg_R'] if x[1]['tn']>=30 else -9)
    noticed.append(f"The {'New York' if best[0]=='NY' else 'London'} session has been the better one to trade ({R(best[1]['avg_R'])} a trade).")
    if good: noticed.append(f"Best level so far: [[{good[0][0]}]] ({R(good[0][1]['avg_R'])} a trade over {good[0][1]['tn']}). Worst: [[{good[-1][0]}]] ({R(good[-1][1]['avg_R'])}).")
    noticed.append(f"Busiest day of the week: {max(wd,key=lambda x:x[1])[0]}; quietest: {min(wd,key=lambda x:x[1])[0]}.")
    noticed.append(f"When price pokes past a level, it comes back {pct(st['back'],st['n'])} of the time, and the trend clearly flips after {pct(st['flip'],st['back'])} of those.")
    body=note_head('market')+f"# {name}\n\nEverything the brain knows about {name}, re-measured from all the data every run.\n\n## What it has noticed\n\n"+'\n'.join('- '+x for x in noticed)+"\n\n## A normal day\n\n"+f"- Whole day: moves about {avg('range',ds):,.1f} from high to low\n- [[Asia high|Asia session]]: {avg('asia',ds):,.1f} · [[London (session)|London]]: {avg('london',ds):,.1f} · [[New York (session)|New York]]: {avg('ny',ds):,.1f}\n- Finished up on {pct(up,len(ds))} of {len(ds)} days\n- By weekday: "+', '.join(f"{d} {r:,.0f}" for d,r in wd)+"\n\n## Sweeps by session\n\n"+HEAD+row('London (session)',by_sess['London'])+'\n'+row('New York (session)',by_sess['NY'])+f"\n\n{LEXPLAIN}\n\n## Sweeps by level\n\n"+HEAD+'\n'.join(row(L,x) for L,x in by_lvl)+"\n\n## How this has changed\n\n"+('\n'.join('- '+h for h in hist) if hist else f'- {TODAY}: first measurement. Changes will be logged here as more data comes in.')+f"\n\nSee also: [[Home]] · [[The main strategy]] · [[Questions]]"
    write('Markets',name,body)
# ---- levels
for L in sorted(set(c['L'] for c in C)):
    xs=[c for c in C if c['L']==L]; st=stats(xs)
    facts={'flip_rate':st['flip_rate'],'back_rate':st['back_rate'],'avg_R':st['avg_R']}
    hist=remember('level:'+L,facts,{'flip_rate':'flip rate','back_rate':'came-back rate','avg_R':'result per trade'})
    body=note_head('level')+f"# {L}\n\n{what_it_means(st,'trading sweeps of '+L.lower())}\n\n## Everywhere\n\n"+HEAD+row(L,st,False)+"\n\n## By market\n\n"+HEAD+'\n'.join(row(MN[s],stats([c for c in xs if c['inst']==s])) for s in MN)+"\n\n## By session\n\n"+HEAD+'\n'.join(row(n,stats([c for c in xs if c['session']==k])) for k,n in (('London','London (session)'),('NY','New York (session)')))+f"\n\n{LEXPLAIN}\n\n## How this has changed\n\n"+('\n'.join('- '+h for h in hist) if hist else f'- {TODAY}: first measurement.')+"\n\nPart of [[Key levels]]. Swept levels are explained in [[Sweep]]."
    write('Levels',L,body)
# ---- sessions
for k,n,blurb in (('London','London (session)','2am to 5am New York time.'),('NY','New York (session)','8:30 to 11:30am New York time, around the US stock market open.')):
    xs=[c for c in C if c['session']==k]; st=stats(xs)
    hist=remember('session:'+k,{'flip_rate':st['flip_rate'],'avg_R':st['avg_R']},{'flip_rate':'flip rate','avg_R':'result per trade'})
    hours=sorted(set(c['hour'] for c in xs))
    body=note_head('session')+f"# {n}\n\n{blurb} {what_it_means(st,'this session')}\n\n## By market\n\n"+HEAD+'\n'.join(row(MN[s],stats([c for c in xs if c['inst']==s])) for s in MN)+"\n\n## Hour by hour\n\n"+HEAD+'\n'.join(row(f"{h:02d}:00",stats([c for c in xs if c['hour']==h]),False) for h in hours)+"\n\n## How this has changed\n\n"+('\n'.join('- '+h for h in hist) if hist else f'- {TODAY}: first measurement.')+"\n\nSee [[Trading hours]]."
    write('Sessions',n,body)
# ---- months (never deleted, one per month of history)
ad={r['month']:r for r in BT['adaptive']}; ao={r['month']:r for r in BT['adaptive_ob']}; MS=BT['months']
DV={'fvg_first':'gap first','ob_first':'order block first','both':'London + New York','ny':'New York','london':'London','ny_open':'New York first 90 min','none':'no direction rule','h1':'hourly trend','pd':'sell high, buy low','daily':'same way as yesterday','required':'SMT required','optional':'SMT optional','quality':'important levels','any':'any level','session':'session levels only','eq':'equal highs/lows only','htf':'big levels','instant':'instant snap-back only','all':'all three markets','nq':'Nasdaq only','nq_es':'Nasdaq + S&P','es':'S&P 500 only','pool':'next level','2R':'2× target','3R':'3× target','be1':'stop to entry at +1R'}
rl=lambda r:', '.join(DV.get(v,v) for k,v in r.items() if not (k=='manage' and v=='none'))
for i,m in enumerate(MS):
    xs=[c for c in C if c['month']==m]; st=stats(xs); a=ad.get(m); o=ao.get(m); warm=i<BT['look']
    per={s:stats([c for c in xs if c['inst']==s]) for s in MN}
    nav=(f"[[{MS[i-1]}]] ← " if i else '')+f"**{m}**"+(f" → [[{MS[i+1]}]]" if i<len(MS)-1 else '')
    body=note_head('month')+f"# {m}\n\n{nav}\n\n## What the strategies did\n\n"+(f"- Warm-up month: used only as history for picking rules.\n" if warm else '')+f"- [[The main strategy]] ({rl(a['rules']) if a and not warm else 'starting rules'}): {a['n'] if a else 0} trades, **{R(a['R']) if a else '–'}**\n- [[The order-block strategy]] ({rl(o['rules']) if o and not warm else 'starting rules'}): {o['n'] if o else 0} trades, **{R(o['R']) if o else '–'}**\n"+(f"- The main strategy's settings changed this month.\n" if a and a.get('changed') else '')+"\n## The market that month\n\n"+HEAD+'\n'.join(row(MN[s],per[s]) for s in MN)+f"\n\n{st['n']} level sweeps in total. Year: [[{m[:4]}]]."
    write('Months',m,body)
for y in sorted(set(m[:4] for m in MS)):
    ms=[m for m in MS if m.startswith(y)]; a=[ad[m] for m in ms if m in ad and MS.index(m)>=BT['look']]; o=[ao[m] for m in ms if m in ao and MS.index(m)>=BT['look']]
    body=note_head('year')+f"# {y}\n\n| month | main strategy | order-block |\n|---|---|---|\n"+'\n'.join(f"| [[{m}]] | {R(ad[m]['R'])} ({ad[m]['n']}) | {R(ao[m]['R'])} ({ao[m]['n']}) |" for m in ms)+f"\n\nTest months only: main {R(sum(x['R'] for x in a))}, order-block {R(sum(x['R'] for x in o))}."
    write('Months',y,body)
# ---- lab runs: one note per run, never deleted
lab_name=f"Lab run {TODAY}"; S=BT['sum']
write('Lab',lab_name,note_head('lab-run')+f"# {lab_name}\n\nTested {BT['n_variants']:,} versions of the rules on {BT['sessions']} days ({span}), re-picking every month from the previous {BT['look']} months.\n\n| on the {S['base']['months']} test months | trades | total | worst drop |\n|---|---|---|---|\n| main, fixed | {S['base']['n']} | {R(S['base']['R'])} | {S['base']['dd']}R |\n| main, adjusting | {S['adaptive']['n']} | {R(S['adaptive']['R'])} | {S['adaptive']['dd']}R |\n| order-block, fixed | {S['base_ob']['n']} | {R(S['base_ob']['R'])} | {S['base_ob']['dd']}R |\n| order-block, adjusting | {S['adaptive_ob']['n']} | {R(S['adaptive_ob']['R'])} | {S['adaptive_ob']['dd']}R |\n\nPicked for next month: main = {rl(BT['now']['chain']['rules']) if BT['now'].get('chain') else 'no change'}; order-block = {rl(BT['now']['ob']['rules']) if BT['now'].get('ob') else 'no change'}.\n\nEarlier runs are in the Lab folder. Lessons: [[Lessons]].")
# ---- questions the brain keeps asking
def q(key,title,ask,answer_fn):
    ans,detail=answer_fn(); prev=state['answers'].get(key); hist=state['history'].setdefault('q:'+key,[])
    if prev and prev!=ans: hist.append(f"{TODAY}: answer changed from \"{prev}\" to \"{ans}\"")
    state['answers'][key]=ans
    write('Questions',title,note_head('question').replace('---\n#','---\n#',1).rstrip('-\n')+f"\nanswer: \"{ans}\"\n---\n"+f"# {title}\n\n**Question:** {ask}\n\n**Current answer:** {ans}\n\n{detail}\n\n## How the answer has changed\n\n"+('\n'.join('- '+h for h in hist[-20:]) if hist else f'- {TODAY}: first answer.')+"\n\nAll questions: [[Questions]].")
    return title,ans
def cmp(a,b,la,lb,thing):
    A,B=stats(a),stats(b)
    if min(A['tn'],B['tn'])<30: return 'not enough data yet',f"{la}: {A['tn']} trades, {lb}: {B['tn']} trades."
    diff=A['avg_R']-B['avg_R']; ans=('yes' if diff>0.1 else 'no' if diff<-0.1 else 'unclear, the difference is small')
    return ans,f"{la}: {R(A['avg_R'])} a trade ({A['tn']} trades). {lb}: {R(B['avg_R'])} a trade ({B['tn']} trades)."
QS=[q('smt','Does SMT help','Do trades where the other market disagreed ([[SMT]]) do better?',lambda:cmp([c for c in C if c['smt']],[c for c in C if not c['smt']],'With SMT','Without','SMT')),
 q('ny','Is New York better than London','Is the [[New York (session)|New York session]] better to trade than [[London (session)|London]]?',lambda:cmp([c for c in C if c['session']=='NY'],[c for c in C if c['session']=='London'],'New York','London','')),
 q('daily','Does trading with yesterday help','Do trades in the same direction as yesterday do better?',lambda:cmp([c for c in C if c['daily']],[c for c in C if not c['daily']],'Same way as yesterday','Against it','')),
 q('h1','Does the hourly trend help','Do trades that agree with the hourly trend do better?',lambda:cmp([c for c in C if c['h1']],[c for c in C if not c['h1']],'With the hourly trend','Against it','')),
 q('big','Do big levels beat small ones','Do sweeps of the big [[Session levels|session levels]] do better than sweeps of small 5-minute highs and lows?',lambda:cmp([c for c in C if c['level_kind']=='session'],[c for c in C if c['level_tf']=='5m' and c['level_kind']=='swing'],'Session levels','5-minute highs and lows','')),
 q('nqes','Is the Nasdaq better than the S&P 500','Does the strategy work better on the [[Nasdaq]] than the [[S&P 500]]?',lambda:cmp([c for c in C if c['inst']=='NQ'],[c for c in C if c['inst']=='ES'],'Nasdaq','S&P 500','')),
 q('edge','Is there an edge yet','After adjusting every month, does either strategy make money on months it wasn\'t tuned on?',lambda:(('yes, the order-block strategy' if S['adaptive_ob']['R']>0 else 'yes, the main strategy' if S['adaptive']['R']>0 else 'not yet'),f"Main: {R(S['adaptive']['R'])} over {S['adaptive']['n']} trades. Order-block: {R(S['adaptive_ob']['R'])} over {S['adaptive_ob']['n']} trades. Over {S['adaptive']['months']} test months."))]
write('Questions','Questions',note_head('questions')+"# Questions\n\nThe questions the brain keeps asking itself. Every run it re-checks each one against all the data, and logs when an answer changes. Add your own in your notes below and they'll be picked up by [[Ask Claude]].\n\n| question | current answer |\n|---|---|\n"+'\n'.join(f"| [[{t}]] | {a} |" for t,a in QS))
# ---- the desk's agents: one note each, their own lessons and track record
AG=[('Scout','![[scout.svg|40]]','Hunts for the strongest setups.'),('Sceptic','![[sceptic.svg|40]]','Tries to find why each trade will fail.'),('Risk','![[risk.svg|40]]','Protects the account.'),('Chief','![[chief.svg|40]]','Reads the other three and makes the call.')]
calls=[json.loads(l) for l in open(os.path.join(ROOT,'data','desk_calls.jsonl'))] if os.path.exists(os.path.join(ROOT,'data','desk_calls.jsonl')) else []
farmd=json.load(open(os.path.join(ROOT,'data','farm.json'))); outc={t['key']:t['R'] for t in farmd['trades'] if t.get('route')=='feed' and t.get('key')}
for name,emo,job in AG:
    mp=os.path.join(ROOT,'data','agent_memory',name+'.json'); mem=json.load(open(mp)) if os.path.exists(mp) else {'lessons':[],'calls':[]}
    rows=[]
    for c in calls:
        v=c['chief'].get('decision') if name=='Chief' else (c.get('views',{}).get(name) or {}).get('view'); R_=outc.get(c['key'])
        rows.append((c['when'],c['setup'],v,R_))
    done=[r for r in rows if r[3] is not None]; right=sum(1 for r in done if (r[2]=='take')==(r[3]>0))
    body=note_head('agent')+f"# {name}\n\n{emo}\n\n{job} One of the four AI agents on [[The desk]]. It has its own memory and rewrites its own lessons every Friday from how its calls turned out.\n\n## Its lessons (written by itself)\n\n"+('\n'.join('- '+l for l in mem['lessons']) or '- None yet. Lessons start once it has made calls and seen the results.')+f"\n\n## Track record\n\n{len(rows)} calls, {len(done)} with a result, right {pct(right,len(done))}.\n\n| when | setup | said | result |\n|---|---|---|---|\n"+'\n'.join(f"| {w} | {st_} | {v} | {R(r) if r is not None else 'pending'} |" for w,st_,v,r in rows[-40:])
    write('Agents',name,body)
write('Agents','The desk',note_head('desk')+"# The desk\n\nFour AI agents judge every setup the rules find (about 2 to 3 a day across the Nasdaq, S&P 500, Dow and Russell 2000): [[Scout]], [[Sceptic]], [[Risk]] and [[Chief]]. Each thinks separately, with its own memory. The Chief decides take or skip.\n\nThe desk only works live, never on old prices, because an AI has already read about the past. Every setup is played out whether the desk takes it or not, so its picks can be scored against simply taking everything.\n\nThis is the experiment behind the question: **can an AI trade?**\n\nSee also [[Home]] and [[Questions]].")
# ---- dashboards (Obsidian Bases) and graph colours
os.makedirs(os.path.join(VAULT,'Dashboards'),exist_ok=True)
open(os.path.join(VAULT,'Dashboards','Trades.base'),'w').write("""filters:
  and:
    - file.inFolder("Trades")
properties:
  r:
    displayName: "Result (R)"
  market_name:
    displayName: Market
views:
  - type: table
    name: All trades
    groupBy:
      property: strategy
      direction: ASC
    order:
      - file.name
      - date
      - market_name
      - direction
      - session
      - grade
      - r
    summaries:
      r: Sum
  - type: table
    name: Losses to learn from
    filters:
      and:
        - 'r < 0'
    order:
      - file.name
      - date
      - market_name
      - strategy
      - grade
      - r
    summaries:
      r: Sum
  - type: table
    name: Winners
    filters:
      and:
        - 'r > 0'
    order:
      - file.name
      - date
      - market_name
      - strategy
      - r
    summaries:
      r: Average
""")
open(os.path.join(VAULT,'Dashboards','Questions.base'),'w').write("""filters:
  and:
    - file.inFolder("Questions")
    - 'file.name != "Questions"'
properties:
  answer:
    displayName: Current answer
views:
  - type: table
    name: What the brain thinks
    order:
      - file.name
      - answer
      - updated
""")
os.makedirs(os.path.join(VAULT,'.obsidian'),exist_ok=True)
gp=os.path.join(VAULT,'.obsidian','graph.json')
if not os.path.exists(gp):
    rgb=lambda h:int(h.lstrip('#'),16)
    json.dump({"colorGroups":[{"query":f"path:{p}","color":{"a":1,"rgb":rgb(c)}} for p,c in (("Days","#E6B54A"),("Trades","#3FBF7F"),("Markets","#5B8DEF"),("Levels","#8F84C9"),("Questions","#F59A3E"),("Agents","#E46FD8"),("Months","#9C7A2E"),("Ideas","#4FC3D9"),("Rules","#ECE6D8"))],"showOrphans":True},open(gp,'w'),indent=1)
# ---- home
notes=sum(len([f for f in fs if f.endswith('.md')]) for _,_,fs in os.walk(VAULT))
words=sum(len(open(os.path.join(dp,f)).read().split()) for dp,_,fs in os.walk(VAULT) for f in fs if f.endswith('.md'))
state['growth']=[g for g in state['growth'] if g['date']!=TODAY]+[dict(date=TODAY,notes=notes,words=words,new=len(new_notes))]
latest=sorted([os.path.join(dp,f) for dp,_,fs in os.walk(VAULT) for f in fs if f.endswith('.md') and '.argon' not in dp],key=os.path.getmtime)[-1:]
days=sorted(f[:-3] for f in os.listdir(os.path.join(VAULT,'Days'))) if os.path.isdir(os.path.join(VAULT,'Days')) else []
write('',"Home",f"---\ntype: home\nupdated: {TODAY}\n---\n# Argon's brain\n\nThis vault grows every time Argon runs. Day notes, trades, months and lab runs pile up and are never deleted. Living notes about each [[Questions|question]], market, level and session are re-measured from all the data each time, and their history sections show how the answers have shifted.\n\nAnything you write under the line at the bottom of a note is yours and is never changed.\n\n## Start here\n\n- Rules now: [[{[f[:-3] for f in sorted(os.listdir(os.path.join(VAULT,'Rules'))) if f.startswith('Rulebook')][-1] if os.path.isdir(os.path.join(VAULT,'Rules')) else 'Rulebook v0.4'}]] · [[Lessons]] · [[Changelog]]\n- Open questions: [[Questions]] · dashboards: ![[Questions.base]]\n- Every trade, with totals: [[Trades.base]]\n- The AI desk: [[The desk]] · [[Scout]] · [[Sceptic]] · [[Risk]] · [[Chief]]\n- Markets: [[Nasdaq]] · [[S&P 500]] (the Dow and Russell 2000 only have recent data so far)\n- Sessions: [[London (session)]] · [[New York (session)]]\n- History: "+' · '.join(f'[[{y}]]' for y in sorted(set(m[:4] for m in MS)))+f"\n- Latest day: {('[['+days[-1]+']]') if days else '–'} · Latest lab run: [[{lab_name}]]\n\n## How big the brain is\n\n| date | notes | words | new this run |\n|---|---|---|---|\n"+'\n'.join(f"| {g['date']} | {g['notes']} | {g['words']:,} | {g['new']} |" for g in state['growth'][-30:])+"\n")
json.dump(state,open(STATE,'w'),indent=1)
print('brain:',dict(written),'new notes',len(new_notes),'total notes',notes,'words',words)
