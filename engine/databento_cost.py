"""Price check ONLY (downloads nothing): what would 2010-2020 NQ and ES 1-minute data cost on Databento?
Writes data/databento_cost.json. Needs the DATABENTO_API_KEY GitHub secret."""
import os,sys,json,datetime as dt
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import fetch_databento as fd
if not fd.KEY: print('No DATABENTO_API_KEY'); sys.exit(0)
rows=[];total=0.0
for m in ('NQ','ES'):
    for y in range(2010,2021):
        a=f'{y}-06-07' if y==2010 else f'{y}-01-01'; b=f'{y+1}-01-01'
        try: c=float(fd.call('metadata.get_cost',fd.params(fd.MARKETS[m],a,b)))
        except Exception as e: c=None; print(m,y,'error',e)
        rows.append(dict(market=m,year=y,start=a,end=b,usd=c)); total+=c or 0
out=dict(checked=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),schema='ohlcv-1m',dataset='GLBX.MDP3',total_usd=round(total,2),rows=rows)
json.dump(out,open(os.path.join(fd.ROOT,'data','databento_cost.json'),'w'),indent=1); print('total $%.2f'%total)
