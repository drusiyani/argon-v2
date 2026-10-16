import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
"""Save fresh futures tape every day (Yahoo keeps only ~60 days of 5m, ~35 of 2m, so we keep our own copy),
and pull the latest full month of 1-minute HistData for the long backtest."""
import json,urllib.request,urllib.parse,datetime as dt,re,time,glob
UA={'User-Agent':'Mozilla/5.0'}
def get(url,data=None,ref=None):
    h=dict(UA); 
    if ref: h['Referer']=ref
    req=urllib.request.Request(url,data=data,headers=h); return urllib.request.urlopen(req,timeout=60).read()
def merge(path,new):
    """Keep every bar we've ever seen: merge new Yahoo bars into the stored file by timestamp."""
    try: old=json.load(open(path))
    except Exception: old=None
    if not old: json.dump(new,open(path,'w')); return
    o=old['chart']['result'][0]; n=new['chart']['result'][0]
    rows={}
    for src in (o,n):
        q=src['indicators']['quote'][0]
        for i,t in enumerate(src['timestamp']): rows[t]=[q[k][i] for k in ('open','high','low','close','volume')]
    ts=sorted(rows); q=o['indicators']['quote'][0]
    for j,k in enumerate(('open','high','low','close','volume')): q[k]=[rows[t][j] for t in ts]
    o['timestamp']=ts; json.dump(old,open(path,'w'))
def futures():
    for sym in ('NQ','ES','YM','RTY'):
        for iv,rng,suf in (('5m','60d',''),('2m','60d','2')):
            d=json.loads(get(f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}=F?interval={iv}&range={rng}'))
            merge(os.path.join(ROOT,'data','futures',f'{sym}F{suf}.json'),d); time.sleep(1)
def histdata_month(y,m):
    for pair in ('NSXUSD','SPXUSD'):
        out=os.path.join(ROOT,'data','histdata',f'{pair}_{y}{m:02d}.zip')
        if os.path.exists(out): continue
        page=f'https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{pair.lower()}/{y}/{m}'
        tk=re.search(r'id="tk" value="([^"]+)"',get(page).decode()).group(1)
        body=urllib.parse.urlencode(dict(tk=tk,date=y,datemonth=f'{y}{m:02d}',platform='ASCII',timeframe='M1',fxpair=pair)).encode()
        z=get('https://www.histdata.com/get.php',body,page)
        if z[:2]==b'PK': open(out,'wb').write(z)
        time.sleep(1)
def backfill():
    """First run only: 2024 comes as one yearly file per market, later months one file each."""
    for pair in ('NSXUSD','SPXUSD'):
        out=os.path.join(ROOT,'data','histdata',f'{pair}_2024.zip')
        if not os.path.exists(out):
            page=f'https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{pair.lower()}/2024'
            tk=re.search(r'id="tk" value="([^"]+)"',get(page).decode()).group(1)
            z=get('https://www.histdata.com/get.php',urllib.parse.urlencode(dict(tk=tk,date=2024,datemonth=2024,platform='ASCII',timeframe='M1',fxpair=pair)).encode(),page)
            if z[:2]==b'PK': open(out,'wb').write(z)
    d=dt.date(2025,1,1); end=dt.date.today().replace(day=1)
    while d<end: histdata_month(d.year,d.month); d=(d+dt.timedelta(days=32)).replace(day=1)
if __name__=='__main__':
    import sys
    os.makedirs(os.path.join(ROOT,'data','futures'),exist_ok=True); os.makedirs(os.path.join(ROOT,'data','histdata'),exist_ok=True)
    futures()
    if 'backfill' in sys.argv: backfill()
    if 'monthly' in sys.argv:
        t=dt.date.today().replace(day=1)-dt.timedelta(days=1); histdata_month(t.year,t.month)
