"""Download DAILY bars (DAILY_SET=gc_zn: gold + 10y Treasury, front by volume; DAILY_SET=fx: five CME currency futures,
front by volume plus nearest/next by calendar for the carry basis), June 2010 to end of
last month, into data/extra/ (not read by the book or farm). For the trend-sleeve lab idea.
Quote first, stop above DAILY_MAX_USD (default $1; quoted $0.10 on 28 Nov 2026). Each file checked (symbol, no
duplicate days, enough rows) before saving; never downloaded twice (data/extra/MANIFEST.json)."""
import os,sys,json,gzip,hashlib,datetime as dt
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import fetch_databento as fd
OUT=os.path.join(fd.ROOT,'data','extra'); os.makedirs(OUT,exist_ok=True); MAN=os.path.join(OUT,'MANIFEST.json')
MAX=float(os.environ.get('DAILY_MAX_USD','1'))
A='2010-06-07'; B=dt.date.today().replace(day=1).isoformat()
FX=('6E','6J','6B','6A','6C')   # euro, yen, pound, Aussie, Canadian dollar vs USD (CME currency futures)
SETS={'gc_zn':[('GC','GC.v.0','GC_daily.csv.gz'),('ZN','ZN.v.0','ZN_daily.csv.gz')],
      'fx':[(m,f'{m}.v.0',f'{m}_daily.csv.gz') for m in FX]+[(m,f'{m}.c.{i}',f'{m}_c{i}_daily.csv.gz') for m in FX for i in (0,1)]}
JOBS=SETS[os.environ.get('DAILY_SET','gc_zn')]
sha=lambda p:hashlib.sha256(open(p,'rb').read()).hexdigest()
P=lambda sym:dict(fd.params(sym,A,B),schema='ohlcv-1d')
def check(raw,sym):
    lines=raw.decode().splitlines();h=lines[0].split(',');it,isym=h.index('ts_event'),h.index('symbol');ts=[];syms=set()
    for ln in lines[1:]: r=ln.split(',');ts.append(r[it][:10]);syms.add(r[isym])
    if syms!={sym}: return None,f'symbols {sorted(syms)[:3]}'
    if len(set(ts))!=len(ts): return None,'duplicate days'
    if len(ts)<3500: return None,f'only {len(ts)} rows'
    return dict(rows=len(ts),first=min(ts),last=max(ts),schema='ohlcv-1d'),None
if __name__=='__main__':
    if not fd.KEY: print('No DATABENTO_API_KEY'); sys.exit(1)
    man=json.load(open(MAN)) if os.path.exists(MAN) else {'files':{}}
    todo=[j for j in JOBS if not (j[2] in man['files'] and os.path.exists(os.path.join(OUT,j[2])))]
    if not todo: print('already downloaded'); sys.exit(0)
    cost=sum(float(fd.call('metadata.get_cost',P(s))) for m,s,n in todo); print(f'quote ${cost:.4f} for {len(todo)} files')
    if cost>MAX: print('over the cap, stopping'); sys.exit(1)
    bad=0
    for m,s,name in todo:
        raw=fd.call('timeseries.get_range',dict(P(s),encoding='csv',pretty_px='true',pretty_ts='true',map_symbols='true',compression='none'),raw=True)
        info,err=check(raw,s)
        if not info: print('check failed',name,err); bad+=1; continue
        p=os.path.join(OUT,name)
        with gzip.open(p,'wb') as f: f.write(raw)
        man['files'][name]=dict(info,sha256=sha(p)); json.dump(man,open(MAN,'w'),indent=1); print('ok',name,info)
    man['daily_quote_usd']=round(cost,4); json.dump(man,open(MAN,'w'),indent=1); sys.exit(1 if bad else 0)
