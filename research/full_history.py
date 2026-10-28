"""Full-history check of the final portfolio (4 strategies, QuantLab skips FOMC days) vs the old baseline.
$100k start, compounding monthly at a fixed % risk per trade. Jul 2021 - Sep 2026. Mostly in-sample: see LOCKBOX.md."""
import os,sys,json,collections
os.environ['ARGON_FULL']='1'; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import common as c
sys.argv=['x']; c.OPEN=False   # run_all refuses to import in test mode with the lock open; data range is already set by ARGON_FULL
import run_all as ra
c.OPEN=True
ra.MONTHS=c.months_between(c.FIRST_MONTH,c.FULL_END); ra.MSET=set(ra.MONTHS)
out={}
for name,over in (('baseline',{}),('final (QuantLab skips FOMC)',{'quantlab':{'skip_fomc':True}})):
    for cx in (1.0,2.0):
        s=ra.series(ra.book(cx,over),cx)
        for risk in (0.75,1.0):
            eq=100000.0;pk=eq;dd=0;yr=collections.OrderedDict();start={}
            for m,v in zip(ra.MONTHS,s):
                y=m[:4]; start.setdefault(y,eq); eq*=1+v*risk/100; pk=max(pk,eq); dd=min(dd,eq/pk-1); yr[y]=eq
            prev=100000.0;years={}
            for y,e in yr.items(): years[y]=dict(pct=round((e/start[y]-1)*100,1),usd=round(e-start[y])); 
            neg=sum(1 for v in s if v<0)
            out[f'{name}|{cx}x costs|{risk}%']=dict(sharpe=round(c.sharpe(s),2),R=round(sum(s),1),final=round(eq),a_year=round(((eq/1e5)**(12/len(s))-1)*100,1),
                worst_drop=round(dd*100,1),losing_months=f'{neg}/{len(s)}',worst_month_R=round(min(s),1),years=years)
json.dump(out,open(c.ROOT+'/research/results/full_history.json','w'),indent=1)
for k,v in out.items(): print(k,json.dumps(v))
