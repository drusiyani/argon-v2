"""Stats cards for the front page: each v2 strategy and the whole book (cost rule on), in two eras:
2021-07..2026-09 (the backtest) and 2011-01..2020-12 (the never-seen lockbox, opened once on 28 Oct 2026).
Run once per data folder; writes results/cards_<data>.json."""
import os,sys,json,collections,statistics as stt
os.environ['ARGON_FULL']='1'; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import common as c
ERA=('2011-01','2020-12') if c.DATA!='databento' else ('2021-07','2026-09'); MS=c.months_between(*ERA)
P=dict(quantlab=c.walkforward(c.quantlab('NQ',skip_fomc=True)),noiseband=c.walkforward(c.noiseband('NQ')),atrband=c.atrband('NQ'),expiry=c.opex('NQ')+c.opex('ES'))
def stats(ts,risk=1.0):
    ts=[t for t in ts if ERA[0]<=t['month']<=ERA[1] and t['cost']<=0.10]
    mm=collections.defaultdict(float)
    for t in ts: mm[t['month']]+=t['gross']-t['cost']
    s=[mm.get(m,0.0) for m in MS]; dn=[min(0,v) for v in s]
    eq=1.0;pk=1.0;dd=0;curve=[]
    for m,v in zip(MS,s): eq*=1+v*risk/100;pk=max(pk,eq);dd=min(dd,eq/pk-1);curve.append([m,round(eq*1e5)])
    wins=sum(1 for t in ts if t['gross']-t['cost']>0); sd=stt.stdev(s) if len(s)>1 else 0; dsd=(sum(x*x for x in dn)/len(dn))**.5
    return dict(trades=len(ts),win_rate=round(100*wins/max(1,len(ts)),1),R=round(sum(s),1),R_before_costs=round(sum(t['gross'] for t in ts),1),
                sharpe=round(stt.mean(s)/sd*12**.5,2) if sd else None,sortino=round(stt.mean(s)/dsd*12**.5,2) if dsd else None,
                worst_drop=round(dd*100,1),final=round(eq*1e5),losing_months=sum(1 for v in s if v<0),months=len(s),curve=curve)
out=dict(era=ERA,strategies={k:{x:y for x,y in stats(v).items() if x!='curve'} for k,v in P.items()},book=stats([t for v in P.values() for t in v]))
json.dump(out,open(f'{c.ROOT}/research/results/cards_{c.DATA}.json','w')); print(c.DATA,out['book']['sharpe'],out['book']['final'],{k:v['sharpe'] for k,v in out['strategies'].items()})
