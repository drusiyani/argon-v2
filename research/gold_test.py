"""The v2 book's rules, unchanged, on GOLD futures (GC), Oct 2023 - Sep 2026: data Argon had never seen (bought 30 Oct 2026, $3.84).
Same New York clock (9:30-16:00), same walk-forward, the cost rule, 3 ticks of cost a round trip. The expiry trade is left out
(it is about stock-index options). Information only: gold is not being added to the book."""
import os,sys,json,collections
os.environ['ARGON_FULL']='1'; os.environ['ARGON_DATA']='extra'; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import common as c
P=dict(quantlab=c.walkforward(c.quantlab('GC',skip_fomc=True)),noiseband=c.walkforward(c.noiseband('GC')),atrband=c.atrband('GC'))
ms=c.months_between('2024-04','2026-09')     # first 6 months are warm-up for the walk-forward re-pick
out={}
def stats(ts):
    ts=[t for t in ts if t['month'] in ms and t['cost']<=0.10];mm=collections.defaultdict(float);yr=collections.defaultdict(float)
    for t in ts: r=t['gross']-t['cost'];mm[t['month']]+=r;yr[t['month'][:4]]+=r
    s=[mm.get(m,0.0) for m in ms];eq=1.0;pk=1.0;dd=0
    for v in s: eq*=1+v/100;pk=max(pk,eq);dd=min(dd,eq/pk-1)
    return dict(trades=len(ts),win=round(100*sum(1 for t in ts if t['gross']-t['cost']>0)/max(1,len(ts)),1),R=round(sum(s),1),before_costs=round(sum(t['gross'] for t in ts),1),
                sharpe=round(c.sharpe(s),2),final=round(eq*1e5),worst=round(dd*100,1),years={y:round(v,1) for y,v in sorted(yr.items())})
for k,v in P.items(): out[k]=stats(v)
out['book']=stats([t for v in P.values() for t in v])
json.dump(out,open(c.ROOT+'/research/results/gold.json','w'),indent=1)
for k,v in out.items(): print(k,json.dumps(v))
