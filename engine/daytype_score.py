"""Score the three pre-registered sizing arms (Amendment 4) on the v2 book, from 1 Jan 2027:
  1x (plain book)  |  dumb rule (yesterday's range vs 20-day average)  |  AI day-type forecast (median of 3, limited veto)
Each arm multiplies that day's book R by its size, capped so a day never risks more than 4R in total (size x trades <= 4).
Promotion rule (fixed in advance): after at least 120 scored trading days, the AI arm takes real control only if its Sharpe beats
BOTH other arms by at least +0.15. Writes data/daytype_score.json (and the 3D desk shows the latest call)."""
import os,json,statistics as stt,collections,datetime as dt
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START=os.environ.get('DAYTYPE_START','2027-01-01'); MIN_DAYS=120; MARGIN=0.15; DAY_CAP=4.0
calls={}
p=os.path.join(ROOT,'data','daytype.jsonl')
if os.path.exists(p):
    for ln in open(p):
        try: r=json.loads(ln); calls[r['date']]=r
        except Exception: pass
port=json.load(open(os.path.join(ROOT,'data','portfolio.json'))); daily=port.get('daily_R',{})
def capped(size,n): return min(size,DAY_CAP/max(1,n)) if size>0 else 0.0
arms={'1x':[], 'dumb rule':[], 'AI':[]}; rows=[]; brier=[]
for d,c in sorted(calls.items()):
    if d<START or d not in daily and d>max(daily or ['0']): continue          # day not in the book's data yet
    row=daily.get(d,[0.0,0.0,0,None]); net,gross,n=row[0],row[1],row[2]; trend=row[3] if len(row)>3 else None
    s1,sd,sa=1.0,capped(c['dumb_size'],n),capped(c['ai_size_used'],n)
    arms['1x'].append((d,net*capped(s1,n))); arms['dumb rule'].append((d,net*sd)); arms['AI'].append((d,net*sa))
    tp=c['ai'].get('trend_probability')
    if tp is not None and trend is not None: brier.append((tp/100-trend)**2)        # label = the MARKET's day (Amendment 4b), not the book's result
    rows.append(dict(date=d,trades=n,book_R=net,ai_size=c['ai_size_used'],dumb_size=c['dumb_size'],veto=c['ai'].get('veto'),late=c.get('late')))
# ---- the AI council (Amendment 4b): exploratory, separate from the main arms, judged after at least 250 counted sessions
COUNCIL_MIN=250; cm=collections.defaultdict(lambda:dict(n=0,correct=0,brier=0.0)); wrong=collections.defaultdict(dict); ctr=[]
for d,c in sorted(calls.items()):
    if d<START: continue
    row=daily.get(d); cn=c.get('council') or {}
    if not row or len(row)<4 or row[3] is None or not cn.get('counted'): continue
    y=row[3]; mem=dict(cn.get('members') or {}); mem['council']=dict(trend_probability=cn.get('trend_probability'))
    for k,v in mem.items():
        if not v or v.get('trend_probability') is None: continue
        p=v['trend_probability']/100; x=cm[k]; x['n']+=1; x['correct']+=int((p>=.5)==bool(y)); x['brier']+=(p-y)**2
        if k!='council': wrong[d][k]=int((p>=.5)!=bool(y))
    ctr.append((d,row[0]*capped(cn.get('size',1.0),row[2])))
names=sorted({k for w in wrong.values() for k in w}); overlap={}
for i,a in enumerate(names):
    for b in names[i+1:]:
        both=[(w[a],w[b]) for w in wrong.values() if a in w and b in w]
        if both:
            ea=sum(x for x,_ in both)/len(both); eb=sum(y for _,y in both)/len(both)
            overlap[a+' & '+b]=dict(days=len(both),both_wrong=round(sum(1 for x,y in both if x and y)/len(both),3),expected_if_independent=round(ea*eb,3))
council_out=dict(counted_sessions=len(ctr),min_sessions=COUNCIL_MIN,members={k:dict(sessions=v['n'],accuracy=round(v['correct']/v['n'],3),brier=round(v['brier']/v['n'],3)) for k,v in cm.items() if v['n']},
    error_overlap=overlap,trading_R=round(sum(v for _,v in ctr),2),note='exploratory: never touches the book; judged only after the minimum sessions')

def monthly_sharpe(xs):
    m=collections.defaultdict(float)
    for d,v in xs: m[d[:7]]+=v
    v=list(m.values()); return round(stt.mean(v)/stt.stdev(v)*12**.5,3) if len(v)>1 and stt.stdev(v)>0 else None
res={k:dict(R=round(sum(v for _,v in xs),2),sharpe=monthly_sharpe(xs)) for k,xs in arms.items()}
days=len(rows); verdict='collecting data'
if days>=MIN_DAYS and all(res[k]['sharpe'] is not None for k in res):
    verdict='PROMOTE the AI arm' if res['AI']['sharpe']>=max(res['1x']['sharpe'],res['dumb rule']['sharpe'])+MARGIN else 'AI arm not promoted (stays shadow)'
out=dict(start=START,scored_days=days,min_days=MIN_DAYS,margin=MARGIN,arms=res,ai_trend_brier=round(stt.mean(brier),3) if brier else None,
         brier_note='0.25 = coin flip; lower is better',verdict=verdict,vetos=sum(1 for r in rows if r['veto']),late_days=sum(1 for r in rows if r['late']),
         council=council_out, label='trend day = |close-open| >= 0.6 x (high-low), NQ 9:30-16:00',
         latest_call=calls[max(calls)] if calls else None,updated=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))
json.dump(out,open(os.path.join(ROOT,'data','daytype_score.json'),'w'),indent=1); print('daytype score:',days,'days',res,verdict)
