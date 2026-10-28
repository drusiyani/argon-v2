"""Download the 2010-2020 LOCKBOX: NQ + ES 1-minute candles from Databento, saved to data/lockbox2010/ (NOT data/databento/,
so no backtest or farm run can read it by accident). Verified file by file, never downloaded twice.

Safety, because Databento charges per request:
 - a file already in MANIFEST.json with a matching sha256 is never requested again
 - the price of the missing files is checked first; stops if over LOCKBOX_MAX_USD (default $40)
 - each download is checked (header, symbol, row count, first/last timestamp, no duplicate minutes) BEFORE it is saved;
   a failed check is retried up to 3 times, then that file is reported and skipped
The checks look only at timestamps and counts, never at prices, so nothing about the lockbox's results is seen."""
import os,sys,json,gzip,hashlib,time,datetime as dt
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import fetch_databento as fd
OUT=os.path.join(fd.ROOT,'data','lockbox2010'); os.makedirs(OUT,exist_ok=True); MAN=os.path.join(OUT,'MANIFEST.json')
MAX=float(os.environ.get('LOCKBOX_MAX_USD','40'))
def jobs():
    for m in ('NQ','ES'):
        for y in range(2010,2021):
            yield m,y,(f'{y}-06-07' if y==2010 else f'{y}-01-01'),f'{y+1}-01-01'
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def check(raw,m,y,a,b):
    lines=raw.decode().splitlines(); h=lines[0].split(',')
    need=['ts_event','open','high','low','close','volume','symbol']
    if any(k not in h for k in need): return None,f'bad header {h[:6]}'
    it,isym=h.index('ts_event'),h.index('symbol'); ts=[];syms=set()
    for ln in lines[1:]:
        r=ln.split(','); ts.append(r[it][:16]); syms.add(r[isym])
    n=len(ts)
    if syms!={fd.MARKETS[m]}: return None,f'unexpected symbols {sorted(syms)[:3]}'
    if len(set(ts))!=n: return None,f'{n-len(set(ts))} duplicate minutes'
    low=150000 if y==2010 else 300000
    if n<low: return None,f'only {n} rows (expected > {low})'
    first,last=min(ts),max(ts)
    if first[:10]>(dt.date.fromisoformat(a)+dt.timedelta(days=7)).isoformat(): return None,f'starts late {first}'
    if last[:10]<(dt.date.fromisoformat(b)-dt.timedelta(days=6)).isoformat(): return None,f'ends early {last}'
    return dict(rows=n,first=first,last=last),None
if __name__=='__main__':
    if not fd.KEY: print('No DATABENTO_API_KEY'); sys.exit(1)
    man=json.load(open(MAN)) if os.path.exists(MAN) else {'files':{}}
    todo=[]
    for m,y,a,b in jobs():
        name=f'{m}_{y}.csv.gz'; p=os.path.join(OUT,name); e=man['files'].get(name)
        if e and os.path.exists(p) and sha(p)==e['sha256']: continue          # already have it, verified: never pay twice
        todo.append((m,y,a,b,name,p))
    if not todo: print('all 22 files already downloaded and verified'); sys.exit(0)
    cost=sum(float(fd.call('metadata.get_cost',fd.params(fd.MARKETS[m],a,b))) for m,y,a,b,_,_ in todo)
    print(f'{len(todo)} files to fetch, quoted ${cost:.2f}')
    if cost>MAX: print(f'over the ${MAX:.0f} cap, stopping'); sys.exit(1)
    failed=[]
    for m,y,a,b,name,p in todo:
        for attempt in range(1,4):
            try:
                raw=fd.call('timeseries.get_range',dict(fd.params(fd.MARKETS[m],a,b),encoding='csv',pretty_px='true',pretty_ts='true',map_symbols='true',compression='none'),raw=True)
                info,err=check(raw,m,y,a,b)
            except Exception as ex: info,err=None,repr(ex)[:200]
            if info:
                with gzip.open(p,'wb') as f: f.write(raw)
                man['files'][name]=dict(info,sha256=sha(p),start=a,end=b,bytes=os.path.getsize(p),saved=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))
                json.dump(man,open(MAN,'w'),indent=1)      # save after every file, so a crash never costs a re-download
                print('ok',name,info['rows'],'rows',info['first'],'->',info['last']); break
            print('check failed',name,'attempt',attempt,err); time.sleep(10*attempt)
        else: failed.append(name)
    man['quoted_usd_this_run']=round(cost,2); man['complete']=len(man['files'])==22 and not failed; man['failed']=failed
    json.dump(man,open(MAN,'w'),indent=1)
    print('done:',len(man['files']),'of 22 verified','| failed:',failed or 'none'); sys.exit(1 if failed else 0)
