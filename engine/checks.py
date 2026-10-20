"""Data checks, run before every long test. If the clock is wrong (like the daylight-saving bug in the free data),
the busiest minute of the day won't line up with the 9:30 New York open, and the run stops instead of producing
wrong results. Also counts duplicate minutes and contract roll days. Writes data/checks.json."""
import os,sys,glob,gzip,csv,json,collections,datetime as dt
from zoneinfo import ZoneInfo
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); NY=ZoneInfo('America/New_York')
out={'markets':{},'ok':True}
for s in ('NQ','ES','YM','RTY'):
    files=sorted(glob.glob(os.path.join(ROOT,'data','databento',f'{s}_*.csv.gz')))
    if not files: continue
    vol=collections.defaultdict(dict); seen=set(); dup=0; iid_by_day={}; off={}
    for f in files:
        with gzip.open(f,'rt') as fh:
            r=csv.reader(fh); hdr=next(r); iv=hdr.index('volume'); ii=hdr.index('instrument_id') if 'instrument_id' in hdr else None
            for row in r:
                ts=row[0][:16]
                if ts in seen: dup+=1; continue
                seen.add(ts); d0=ts[:10]
                if d0 not in off: off[d0]=dt.datetime(int(d0[:4]),int(d0[5:7]),int(d0[8:10]),12,tzinfo=dt.timezone.utc).astimezone(NY).utcoffset().total_seconds()/60
                m=int(ts[11:13])*60+int(ts[14:16])+int(off[d0])
                if 540<=m<=575: vol[d0][m]=float(row[iv])                # 9:00-9:35 New York
                if ii is not None and 570<=m<960: iid_by_day.setdefault(d0,row[ii])
    good=tot=0
    for d,v in vol.items():
        if 570 not in v or len(v)<20: continue
        base=sorted(x for k,x in v.items() if k<570); med=base[len(base)//2] if base else 0
        tot+=1; good+=v[570]>2*max(med,1)
    days=sorted(iid_by_day); rolls=sum(1 for a,b in zip(days,days[1:]) if iid_by_day[a]!=iid_by_day[b])
    share=good/tot if tot else 0
    out['markets'][s]=dict(open_aligned=round(share,3),sessions=tot,duplicates=dup,roll_days=rolls,ok=share>=0.8)
    out['ok']=out['ok'] and share>=0.8
    print(s,out['markets'][s])
out['checked']=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%MZ')
json.dump(out,open(os.path.join(ROOT,'data','checks.json'),'w'),indent=1)
if not out['ok']: print('DATA CHECK FAILED: the 9:30 open does not line up. Stopping before any test runs.'); sys.exit(1)
