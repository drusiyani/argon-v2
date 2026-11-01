"""Download 3 years of GOLD futures (GC, front month by volume) 1-minute candles into data/extra/ (not read by the book or farm).
Quote first, stop above EXTRA_MAX_USD (default $10). Each file verified (symbol, rows, no duplicate minutes) before it is saved,
and never downloaded twice (data/extra/MANIFEST.json)."""
import os,sys,json,gzip,hashlib,datetime as dt
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import fetch_databento as fd
OUT=os.path.join(fd.ROOT,'data','extra'); os.makedirs(OUT,exist_ok=True); MAN=os.path.join(OUT,'MANIFEST.json'); MAX=float(os.environ.get('EXTRA_MAX_USD','10'))
SYM='GC.v.0'; JOBS=[('GC',2023,'2023-10-01','2024-01-01'),('GC',2024,'2024-01-01','2025-01-01'),('GC',2025,'2025-01-01','2026-01-01'),('GC',2026,'2026-01-01','2026-10-01')]
sha=lambda p:hashlib.sha256(open(p,'rb').read()).hexdigest()
def check(raw):
    lines=raw.decode().splitlines();h=lines[0].split(',');it,isym=h.index('ts_event'),h.index('symbol');ts=[];syms=set()
    for ln in lines[1:]: r=ln.split(',');ts.append(r[it][:16]);syms.add(r[isym])
    if syms!={SYM}: return None,f'symbols {sorted(syms)[:3]}'
    if len(set(ts))!=len(ts): return None,'duplicate minutes'
    if len(ts)<50000: return None,f'only {len(ts)} rows'
    return dict(rows=len(ts),first=min(ts),last=max(ts)),None
if __name__=='__main__':
    if not fd.KEY: print('No DATABENTO_API_KEY'); sys.exit(1)
    man=json.load(open(MAN)) if os.path.exists(MAN) else {'files':{}}
    todo=[(m,y,a,b,f'{m}_{y}.csv.gz') for m,y,a,b in JOBS if not (f'{m}_{y}.csv.gz' in man['files'] and os.path.exists(os.path.join(OUT,f'{m}_{y}.csv.gz')))]
    if not todo: print('already downloaded'); sys.exit(0)
    cost=sum(float(fd.call('metadata.get_cost',fd.params(SYM,a,b))) for m,y,a,b,_ in todo); print(f'quote ${cost:.2f} for {len(todo)} files')
    man['quote_usd']=round(cost,2)
    if cost>MAX: print('over the cap, stopping'); json.dump(man,open(MAN,'w'),indent=1); sys.exit(1)
    for m,y,a,b,name in todo:
        raw=fd.call('timeseries.get_range',dict(fd.params(SYM,a,b),encoding='csv',pretty_px='true',pretty_ts='true',map_symbols='true',compression='none'),raw=True)
        info,err=check(raw)
        if not info: print('check failed',name,err); continue
        p=os.path.join(OUT,name)
        with gzip.open(p,'wb') as f: f.write(raw)
        man['files'][name]=dict(info,sha256=sha(p)); json.dump(man,open(MAN,'w'),indent=1); print('ok',name,info)
