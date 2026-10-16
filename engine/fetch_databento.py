"""Download real CME futures 1-minute candles from Databento for the four Kronos markets.

Needs a DATABENTO_API_KEY (GitHub secret, or an environment variable on your laptop). Never paste the key anywhere else.
Checks the price before downloading and stops if it would cost more than MAX_USD (default $50; new accounts get $125 free).
Usage:  python engine/fetch_databento.py            -> backfill from 2021 to the end of last month (skips years already saved)
        python engine/fetch_databento.py monthly    -> just add last month
"""
import os,sys,json,gzip,base64,urllib.request,urllib.parse,datetime as dt
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.path.join(ROOT,'data','databento'); os.makedirs(OUT,exist_ok=True)
KEY=os.environ.get('DATABENTO_API_KEY'); MAX_USD=float(os.environ.get('DATABENTO_MAX_USD','50'))
MARKETS={'NQ':'NQ.v.0','ES':'ES.v.0','YM':'YM.v.0','RTY':'RTY.v.0'}   # front month, rolled by volume
BASE='https://hist.databento.com/v0/'
def call(path,params,raw=False):
    q=urllib.parse.urlencode(params); req=urllib.request.Request(BASE+path+'?'+q)
    req.add_header('Authorization','Basic '+base64.b64encode((KEY+':').encode()).decode())
    r=urllib.request.urlopen(req,timeout=600).read(); return r if raw else json.loads(r)
def params(sym,start,end): return dict(dataset='GLBX.MDP3',symbols=sym,stype_in='continuous',schema='ohlcv-1m',start=start,end=end)
def chunks(monthly):
    today=dt.date.today(); last=today.replace(day=1)
    if monthly:
        a=(last-dt.timedelta(days=1)).replace(day=1); yield f'{a:%Y-%m}',a.isoformat(),last.isoformat(); return
    for y in range(2021,today.year+1):
        a=dt.date(y,1,1); b=min(dt.date(y+1,1,1),last)
        if a<b: yield str(y) if b==dt.date(y+1,1,1) else f'{y}-partial',a.isoformat(),b.isoformat()
if __name__=='__main__':
    if not KEY: print('No DATABENTO_API_KEY set, skipping.'); sys.exit(0)
    jobs=[]
    for tag,a,b in chunks('monthly' in sys.argv):
        for m,sym in MARKETS.items():
            path=os.path.join(OUT,f'{m}_{tag}.csv.gz')
            if os.path.exists(path) and 'partial' not in tag: continue
            jobs.append((m,sym,tag,a,b,path))
    cost=sum(float(call('metadata.get_cost',params(sym,a,b))) for m,sym,tag,a,b,path in jobs)
    print(f'{len(jobs)} downloads, estimated cost ${cost:.2f}')
    if cost>MAX_USD: print(f'Over the ${MAX_USD:.0f} limit, stopping. Raise DATABENTO_MAX_USD if you really mean it.'); sys.exit(1)
    for m,sym,tag,a,b,path in jobs:
        data=call('timeseries.get_range',dict(params(sym,a,b),encoding='csv',pretty_px='true',pretty_ts='true',map_symbols='true',compression='none'),raw=True)
        with gzip.open(path,'wb') as f: f.write(data)
        print('saved',os.path.basename(path),len(data)//1024,'KB')
