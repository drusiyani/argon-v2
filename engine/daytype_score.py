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
    net,gross,n=daily.get(d,[0.0,0.0,0])
    s1,sd,sa=1.0,capped(c['dumb_size'],n),capped(c['ai_size_used'],n)
    arms['1x'].append((d,net*capped(s1,n))); arms['dumb rule'].append((d,net*sd)); arms['AI'].append((d,net*sa))
    tp=c['ai'].get('trend_probability')
    if tp is not None and n: brier.append((tp/100-(1.0 if gross>0 else 0.0))**2)
    rows.append(dict(date=d,trades=n,book_R=net,ai_size=c['ai_size_used'],dumb_size=c['dumb_size'],veto=c['ai'].get('veto'),late=c.get('late')))
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
         latest_call=calls[max(calls)] if calls else None,updated=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))
json.dump(out,open(os.path.join(ROOT,'data','daytype_score.json'),'w'),indent=1); print('daytype score:',days,'days',res,verdict)
