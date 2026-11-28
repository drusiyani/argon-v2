"""Price check ONLY (downloads nothing): what would DAILY bars for gold (GC) and 10-year Treasury (ZN) futures cost
on Databento, June 2010 to end of last month? For the trend-sleeve idea. Writes data/databento_cost_daily.json.
Needs the DATABENTO_API_KEY GitHub secret."""
import os,sys,json,datetime as dt
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import fetch_databento as fd
if not fd.KEY: print('No DATABENTO_API_KEY'); sys.exit(0)
a='2010-06-07'; b=dt.date.today().replace(day=1).isoformat(); rows=[]; total=0.0
for m,sym in (('GC','GC.v.0'),('ZN','ZN.v.0')):
    p=dict(fd.params(sym,a,b),schema='ohlcv-1d')
    try: c=float(fd.call('metadata.get_cost',p))
    except Exception as e: c=None; print(m,'error',e)
    rows.append(dict(market=m,symbol=sym,start=a,end=b,usd=c)); total+=c or 0; print(m,c)
out=dict(checked=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),schema='ohlcv-1d',dataset='GLBX.MDP3',total_usd=round(total,4),rows=rows)
json.dump(out,open(os.path.join(fd.ROOT,'data','databento_cost_daily.json'),'w'),indent=1); print('total $%.4f'%total)
