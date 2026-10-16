import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import json, datetime as dt, hashlib, collections
from zoneinfo import ZoneInfo
NY=ZoneInfo("America/New_York")
INSTS=['NQ','ES']; TRADED=['NQ','ES']; PAIR={'NQ':'ES','ES':'NQ'}
TICK={'NQ':0.25,'ES':0.25,'GC':0.1,'SI':0.005}; BUF={'NQ':2.0,'ES':0.75,'GC':0.6,'SI':0.02}
RULES_VERSION='0.2'
SIG=hashlib.sha1(('argon-v2-rules-'+RULES_VERSION).encode()).hexdigest()[:8]
def sess_date(d):
    sd=d.date() if d.hour<18 else d.date()+dt.timedelta(days=1)
    while sd.weekday()>=5: sd+=dt.timedelta(days=1)
    return sd
def load(sym,fn):
    r=json.load(open(fn))['chart']['result'][0]; q=r['indicators']['quote'][0]; out=[]
    for i,t in enumerate(r['timestamp']):
        o,h,l,c,v=q['open'][i],q['high'][i],q['low'][i],q['close'][i],q['volume'][i]
        if None in (o,h,l,c): continue
        d=dt.datetime.fromtimestamp(t,NY)
        out.append(dict(t=t,sd=sess_date(d),m=d.hour*60+d.minute,dow=d.weekday(),o=o,h=h,l=l,c=c,v=v or 0))
    return out
import zipfile,io,glob,bisect
HDS={'NQ':'NSXUSD','ES':'SPXUSD','GC':'XAUUSD','SI':'XAGUSD'}
from array import array
M1={}
# ---- the C++ walker (engine/fast.cpp): same answers, much faster. Falls back to Python if it can't be built.
import ctypes,subprocess
_CPP=None; _LIB=None
def _load_cpp():
    global _CPP
    if os.environ.get('ARGON_NO_CPP'): return None
    src=os.path.join(ROOT,'engine','fast.cpp'); so=os.path.join(ROOT,'engine','fast.so')
    try:
        if not os.path.exists(so) or os.path.getmtime(so)<os.path.getmtime(src):
            subprocess.run(['g++','-O3','-shared','-fPIC','-o',so,src],check=True,capture_output=True)
        lib=ctypes.CDLL(so); f=lib.walk1m; f.restype=ctypes.c_int; global _LIB; _LIB=lib
        D=ctypes.POINTER(ctypes.c_double); I=ctypes.POINTER(ctypes.c_int)
        f.argtypes=[D,D,D,D,D,I,ctypes.c_int,I,I,ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,ctypes.c_double,D]
        _CPP=f
    except Exception as e: print('C++ walker not available, using Python:',e); _CPP=False
    return _CPP
_CPPDATA={}
def _cpp_inputs(s):
    if s not in _CPPDATA:
        bars=BARS[s]['5m']; T,O,H,L,C=M1[s]; k5=k5_of(s); sdi={}
        SD=array('i',[sdi.setdefault(b['sd'],len(sdi)) for b in bars]); SM=array('i',[smin(b['m']) for b in bars])
        D=ctypes.c_double; I=ctypes.c_int; arr=lambda a,t: (t*len(a)).from_buffer(a)
        _CPPDATA[s]=dict(args=(arr(T,D),arr(O,D),arr(H,D),arr(L,D),arr(C,D),arr(k5,I),len(T),arr(SD,I),arr(SM,I),len(bars),smin(15*60+55)),sdi=sdi,keep=(SD,SM))
    return _CPPDATA[s]
def load_hd(sym):
    if os.environ.get('ARGON_NO_CPP') is None:
        r=load_hd_cpp(sym)
        if r is not None: return r
    return load_hd_py(sym)
def load_hd_cpp(sym):
    """Same as load_hd_py, with the line parsing, time zones and 5-minute grouping done in C++ (engine/fast.cpp)."""
    import ctypes
    if _load_cpp() is False or _LIB is None: return None
    D=ctypes.c_double; P=ctypes.POINTER(D)
    _LIB.parse_histdata.restype=ctypes.c_int; _LIB.parse_histdata.argtypes=[ctypes.c_char_p,ctypes.c_long,P,P,P,P,P,ctypes.c_long]
    _LIB.to_5m.restype=ctypes.c_int; _LIB.to_5m.argtypes=[P,P,P,P,P,ctypes.c_long,P,P,P,P,P]
    cols=[array('d') for _ in range(5)]
    for f in sorted(glob.glob(os.path.join(ROOT,'data','histdata',f'{HDS[sym]}_*.zip'))):
        z=zipfile.ZipFile(f); name=[n for n in z.namelist() if n.endswith('.csv')][0]; buf=z.read(name)
        cap=buf.count(b'\n')+1; outs=[(D*cap)() for _ in range(5)]
        n=_LIB.parse_histdata(buf,len(buf),*outs,cap)
        for c,o in zip(cols,outs): c.extend(o[:n])
    n=len(cols[0]); ins=[(D*n).from_buffer(c) for c in cols]
    _LIB.sort_m1.restype=None; _LIB.sort_m1.argtypes=[P,P,P,P,P,ctypes.c_long]
    _LIB.stable_time_sort.restype=None; _LIB.stable_time_sort.argtypes=[P,P,P,P,P,ctypes.c_long]
    _LIB.stable_time_sort(*ins,n)                          # time order, ties kept in file order
    raw5=[(D*n)() for _ in range(5)]                       # 5-minute bars are built from that, like the Python version
    m=_LIB.to_5m(*ins,n,*raw5)
    _LIB.sort_m1(*ins,n); M1[sym]=tuple(cols)              # then the 1-minute candles are sorted the same way Python sorts tuples
    o5=raw5
    out=[]
    for i in range(m):
        k=int(o5[0][i]); d=dt.datetime.fromtimestamp(k,NY)
        if d.weekday()==5 or (d.weekday()==4 and d.hour>=17) or (d.weekday()==6 and d.hour<18): continue
        out.append(dict(t=k,sd=sess_date(d),m=d.hour*60+d.minute,dow=d.weekday(),o=o5[1][i],h=o5[2][i],l=o5[3][i],c=o5[4][i],v=0))
    return out
def load_hd_py(sym):
    rows={}; m1=[]
    for f in sorted(glob.glob(os.path.join(ROOT,'data','histdata',f'{HDS[sym]}_*.zip'))):
        z=zipfile.ZipFile(f); name=[n for n in z.namelist() if n.endswith('.csv')][0]
        for line in io.TextIOWrapper(z.open(name)):
            p=line.strip().split(';')
            if len(p)<5: continue
            ts=dt.datetime.strptime(p[0],'%Y%m%d %H%M%S').replace(tzinfo=NY).timestamp()   # HistData files are New York local time, daylight saving included
            k=int(ts)//300*300; o,h,l,c=float(p[1]),float(p[2]),float(p[3]),float(p[4]); m1.append((int(ts),o,h,l,c))
            r=rows.get(k)
            if r is None: rows[k]=[o,h,l,c]
            else:
                if h>r[1]: r[1]=h
                if l<r[2]: r[2]=l
                r[3]=c
    m1.sort(); M1[sym]=tuple(array('d',[x[i] for x in m1]) for i in range(5))
    out=[]
    for k in sorted(rows):
        o,h,l,c=rows[k]; d=dt.datetime.fromtimestamp(k,NY)
        if d.weekday()==5 or (d.weekday()==4 and d.hour>=17) or (d.weekday()==6 and d.hour<18): continue
        out.append(dict(t=k,sd=sess_date(d),m=d.hour*60+d.minute,dow=d.weekday(),o=o,h=h,l=l,c=c,v=0))
    return out
def load_db(sym):
    """Real CME futures from Databento (if downloaded): CSV with ts_event, open, high, low, close, volume."""
    import gzip,csv,calendar,time
    rows={}; m1=[]
    for f in sorted(glob.glob(os.path.join(ROOT,'data','databento',f'{sym}_*.csv.gz'))):
        for r in csv.DictReader(io.TextIOWrapper(gzip.open(f))):
            ts=calendar.timegm(time.strptime(r['ts_event'][:19],'%Y-%m-%dT%H:%M:%S'))
            o,h,l,c=float(r['open']),float(r['high']),float(r['low']),float(r['close']); v=float(r.get('volume') or 0)
            m1.append((ts,o,h,l,c)); k=ts//300*300; x=rows.get(k)
            if x is None: rows[k]=[o,h,l,c,v]
            else:
                if h>x[1]: x[1]=h
                if l<x[2]: x[2]=l
                x[3]=c; x[4]+=v
    if not m1: return None
    m1=sorted(set(m1)); M1[sym]=tuple(array('d',[x[i] for x in m1]) for i in range(5))
    out=[]
    for k in sorted(rows):
        o,h,l,c,v=rows[k]; d=dt.datetime.fromtimestamp(k,NY)
        if d.weekday()==5 or (d.weekday()==4 and d.hour>=17) or (d.weekday()==6 and d.hour<18): continue
        out.append(dict(t=k,sd=sess_date(d),m=d.hour*60+d.minute,dow=d.weekday(),o=o,h=h,l=l,c=c,v=v))
    return out
# Databento futures if we have them (all four Kronos markets), otherwise the free HistData CFDs (Nasdaq and S&P only)
SOURCE='databento' if all(glob.glob(os.path.join(ROOT,'data','databento',f'{s}_*.csv.gz')) for s in ('NQ','ES','YM','RTY')) else 'histdata'
if SOURCE=='databento':
    INSTS=['NQ','ES','YM','RTY']; TRADED=['NQ','ES','YM','RTY']; PAIR={'NQ':'ES','ES':'NQ','YM':'ES','RTY':'ES'}
    TICK.update({'YM':1.0,'RTY':0.1}); BUF.update({'YM':8.0,'RTY':0.5})
    B5={s:load_db(s) for s in INSTS}
else:
    B5={s:load_hd(s) for s in INSTS}
print('long backtest data:',SOURCE)
B2={}
days=sorted(set.intersection(*[set(b['sd'] for b in B5[s]) for s in INSTS]))
dayset=set(days)
for s in INSTS: B5[s]=[b for b in B5[s] if b['sd'] in dayset]
for s in B2: B2[s]=[b for b in B2[s] if b['sd'] in dayset]
def smin(m): return (m-18*60)%1440   # minutes since 18:00
def resample(bars,mins):
    out=[];cur=None
    for b in bars:
        key=(b['sd'],b['t']//(mins*60))
        if cur is None or cur['key']!=key:
            if cur: out.append(cur)
            cur=dict(key=key,t=key[1]*mins*60,sd=b['sd'],m=b['m'],dow=b['dow'],o=b['o'],h=b['h'],l=b['l'],c=b['c'],v=b['v'],last_t=b['t'])
        else:
            cur['h']=max(cur['h'],b['h']);cur['l']=min(cur['l'],b['l']);cur['c']=b['c'];cur['v']+=b['v'];cur['last_t']=b['t']
    if cur: out.append(cur)
    return out
TF={'5m':5,'15m':15,'1h':60}
BARS={s:{'5m':B5[s],'15m':resample(B5[s],15),'1h':resample(B5[s],60)} for s in INSTS}
def atr(bars,n=14):
    a=[];s=0;q=collections.deque()
    for i,b in enumerate(bars):
        tr=b['h']-b['l'] if i==0 else max(b['h']-b['l'],abs(b['h']-bars[i-1]['c']),abs(b['l']-bars[i-1]['c']))
        q.append(tr);s+=tr
        if len(q)>n: s-=q.popleft()
        a.append(s/len(q))
    return a
ATR={s:{tf:atr(BARS[s][tf]) for tf in TF} for s in INSTS}
# ---------------- events store
EV=[]  # dicts
def ev(**k): return 0
KINDS=['session_open','pool_formed','sweep','manip_leg','smt','swing','structure_break','mss_failed','inducement','fvg_formed','fvg_inverted','ob_formed','ob_mitigated','ob_invalidated','fire','refusal','outcome','ob_entry']
# ---------------- swings & structure per tf
SW={s:{} for s in INSTS}
def swings(s,tf):
    bars=BARS[s][tf]; out=[]; L=R=2
    lastH=lastL=None
    for i in range(L,len(bars)-R):
        b=bars[i]
        if all(b['h']>bars[i-k]['h'] for k in range(1,L+1)) and all(b['h']>=bars[i+k]['h'] for k in range(1,R+1)):
            lab='HH' if lastH is None or b['h']>lastH else 'LH'; lastH=b['h']
            out.append(dict(i=i,t=b['t'],conf_i=i+R,conf_t=bars[i+R]['t'],typ='H',p=b['h'],lab=lab))
        if all(b['l']<bars[i-k]['l'] for k in range(1,L+1)) and all(b['l']<=bars[i+k]['l'] for k in range(1,R+1)):
            lab='LL' if lastL is None or b['l']<lastL else 'HL'; lastL=b['l']
            out.append(dict(i=i,t=b['t'],conf_i=i+R,conf_t=bars[i+R]['t'],typ='L',p=b['l'],lab=lab))
    return out
for s in INSTS:
    for tf in TF:
        SW[s][tf]=swings(s,tf)
        if s in TRADED:
            for w in SW[s][tf]: ev(t=w['t'],inst=s,tf=tf,kind='swing',p=w['p'],lab=w['lab'],typ=w['typ'])
# structure: walk bars; break of last confirmed swing
BRK={s:{} for s in INSTS}
TREND={s:{} for s in INSTS}  # list of (t, trend)
def structure(s,tf):
    bars=BARS[s][tf]; A=ATR[s][tf]; sw=sorted(SW[s][tf],key=lambda w:w['conf_i'])
    j=0; lastH=lastL=None; trend=0; out=[]; tr=[]
    brokeH=brokeL=False
    for i,b in enumerate(bars):
        while j<len(sw) and sw[j]['conf_i']<=i:
            if sw[j]['typ']=='H': lastH=sw[j]; brokeH=False
            else: lastL=sw[j]; brokeL=False
            j+=1
        rng=b['h']-b['l']; disp= rng>=1.3*A[i] and abs(b['c']-b['o'])>=0.55*rng
        if lastH and not brokeH and b['c']>lastH['p']:
            brokeH=True; typ='bos' if trend==1 else 'choch'
            if typ=='choch' and disp: typ='mss'
            trend=1; out.append(dict(i=i,t=b['t'],dir=1,typ=typ,level=lastH['p'],disp=disp,sw_t=lastH['t']))
        if lastL and not brokeL and b['c']<lastL['p']:
            brokeL=True; typ='bos' if trend==-1 else 'choch'
            if typ=='choch' and disp: typ='mss'
            trend=-1; out.append(dict(i=i,t=b['t'],dir=-1,typ=typ,level=lastL['p'],disp=disp,sw_t=lastL['t']))
        tr.append(trend)
    # failed mss: choch/mss reclaimed within 3 bars
    for o in out:
        o['failed']=False
        if o['typ'] in('choch','mss'):
            for k in range(o['i']+1,min(o['i']+4,len(bars))):
                if (o['dir']==1 and bars[k]['c']<o['level']) or (o['dir']==-1 and bars[k]['c']>o['level']): o['failed']=True; o['fail_t']=bars[k]['t']; break
    return out,tr
for s in INSTS:
    for tf in ['5m','15m','1h']:
        BRK[s][tf],TREND[s][tf]=structure(s,tf)
        if s in TRADED and tf!='1h':
            for o in BRK[s][tf]:
                ev(t=o['t'],inst=s,tf=tf,kind='structure_break',p=o['level'],typ=o['typ'],dir=o['dir'],disp=o['disp'],t0=o['sw_t'])
                if o['failed']: ev(t=o['fail_t'],inst=s,tf=tf,kind='mss_failed',p=o['level'],dir=o['dir'],typ=o['typ'])
def trend_at(s,tf,t):
    bars=BARS[s][tf]; tr=TREND[s][tf]; lo,hi=0,len(bars)-1; r=0
    while lo<=hi:
        mid=(lo+hi)//2
        if bars[mid]['t']+TF[tf]*60<=t: r=mid; lo=mid+1
        else: hi=mid-1
    return tr[r]
# inducement: after a 5m bos/mss up, the first confirmed swing low after the break = IDM; mark when taken
SWT={}
for s in TRADED:
    SWT[s]={}
    for typ in 'HL':
        l=[w for w in SW[s]['5m'] if w['typ']==typ]; SWT[s][typ]=([w['t'] for w in l],l)
for s in TRADED:
    bars=BARS[s]['5m']; sw=SW[s]['5m']
    for o in BRK[s]['5m']:
        typ=('L' if o['dir']==1 else 'H'); arr=SWT[s][typ]; j=bisect.bisect_right(arr[0],o['t']); cand=[arr[1][j]] if j<len(arr[1]) else []
        if not cand: continue
        w=cand[0]
        if w['t']-o['t']>3*3600: continue
        taken=None
        for k in range(w['conf_i']+1,min(w['conf_i']+60,len(bars))):
            if (o['dir']==1 and bars[k]['l']<w['p']) or (o['dir']==-1 and bars[k]['h']>w['p']): taken=bars[k]['t']; break
        ev(t=w['t'],inst=s,tf='5m',kind='inducement',p=w['p'],dir=o['dir'],taken=taken,t_end=taken or bars[min(w['conf_i']+60,len(bars)-1)]['t'])
# ---------------- FVG & OB
ZONES={s:[] for s in INSTS}
def zones(s,tf):
    bars=BARS[s][tf]; A=ATR[s][tf]; life={'5m':288,'15m':96}[tf]
    for i in range(2,len(bars)):
        a,c=bars[i-2],bars[i]
        for d in (1,-1):
            if d==1 and c['l']>a['h'] and c['l']-a['h']>=0.15*A[i]: top,bot=c['l'],a['h']
            elif d==-1 and c['h']<a['l'] and a['l']-c['h']>=0.15*A[i]: top,bot=a['l'],c['h']
            else: continue
            z=dict(kind='fvg',tf=tf,dir=d,t=bars[i-1]['t'],top=top,bot=bot,i=i,mit=None,inv=None)
            for k in range(i+1,min(i+life,len(bars))):
                bk=bars[k]
                if z['mit'] is None and ((d==1 and bk['l']<=top) or (d==-1 and bk['h']>=bot)): z['mit']=bk['t']
                if (d==1 and bk['c']<bot) or (d==-1 and bk['c']>top): z['inv']=bk['t']; break
            z['end']=z['inv'] or bars[min(i+life,len(bars)-1)]['t']
            ZONES[s].append(z)
    # OBs from breaks
    for o in BRK[s][tf]:
        if o['typ']=='bos' and not o['disp']: continue
        i=o['i']; d=o['dir']; k=i; ob=None
        while k>max(0,i-12):
            k-=1; b=bars[k]
            if (d==1 and b['c']<b['o']) or (d==-1 and b['c']>b['o']): ob=k; break
        if ob is None: continue
        b=bars[ob]; z=dict(kind='ob',tf=tf,dir=d,t=b['t'],top=b['h'],bot=b['l'],i=ob,brk_t=o['t'],mit=None,inv=None)
        for k in range(i+1,min(i+life,len(bars))):
            bk=bars[k]
            if z['mit'] is None and ((d==1 and bk['l']<=z['top']) or (d==-1 and bk['h']>=z['bot'])): z['mit']=bk['t']; z['mit_i']=k
            if (d==1 and bk['c']<z['bot']) or (d==-1 and bk['c']>z['top']): z['inv']=bk['t']; break
        z['end']=z['inv'] or bars[min(i+life,len(bars)-1)]['t']
        ZONES[s].append(z)
for s in TRADED:
    for tf in ['5m','15m']: zones(s,tf)
    for z in ZONES[s]:
        if z['kind']=='fvg':
            ev(t=z['t'],inst=s,tf=z['tf'],kind='fvg_formed',p=z['top'],q=z['bot'],dir=z['dir'],t_end=z['end'],mit=z['mit'],inv=z['inv'])
            if z['inv']: ev(t=z['inv'],inst=s,tf=z['tf'],kind='fvg_inverted',p=z['top'],q=z['bot'],dir=z['dir'])
        else:
            ev(t=z['t'],inst=s,tf=z['tf'],kind='ob_formed',p=z['top'],q=z['bot'],dir=z['dir'],t_end=z['end'],mit=z['mit'],inv=z['inv'])
            if z['mit']: ev(t=z['mit'],inst=s,tf=z['tf'],kind='ob_mitigated',p=z['top'],q=z['bot'],dir=z['dir'])
            if z['inv']: ev(t=z['inv'],inst=s,tf=z['tf'],kind='ob_invalidated',p=z['top'],q=z['bot'],dir=z['dir'])
# ---------------- pools & sweeps
SESS_IDX={s:collections.defaultdict(list) for s in INSTS}
for s in INSTS:
    for i,b in enumerate(BARS[s]['5m']): SESS_IDX[s][b['sd']].append(i)
LEVELS={}
_wk=collections.defaultdict(list)
for d in days: _wk[d.isocalendar()[:2]].append(d)
PREVWK={d:_wk.get((d-dt.timedelta(days=7)).isocalendar()[:2],[]) for d in days}
DI={d:i for i,d in enumerate(days)}
def session_pools(s,di):
    sd=days[di]; idx=SESS_IDX[s][sd]; bars=BARS[s]['5m']; pools=[]
    if di>0:
        pidx=SESS_IDX[s][days[di-1]]
        pools.append(dict(name='PDH',typ='H',p=max(bars[i]['h'] for i in pidx),t=bars[idx[0]]['t'],kind='session'))
        pools.append(dict(name='PDL',typ='L',p=min(bars[i]['l'] for i in pidx),t=bars[idx[0]]['t'],kind='session'))
    # previous week
    prev=PREVWK.get(sd,[])
    if prev:
        wi=[i for d in prev for i in SESS_IDX[s][d]]
        pools.append(dict(name='PWH',typ='H',p=max(bars[i]['h'] for i in wi),t=bars[idx[0]]['t'],kind='session'))
        pools.append(dict(name='PWL',typ='L',p=min(bars[i]['l'] for i in wi),t=bars[idx[0]]['t'],kind='session'))
    for nm,(a,b_) in {'Asia':(120,360),'London':(480,660)}.items():
        sel=[i for i in idx if a<=smin(bars[i]['m'])<b_]
        if sel:
            endt=bars[sel[-1]]['t']+300
            pools.append(dict(name=nm+' high',typ='H',p=max(bars[i]['h'] for i in sel),t=endt,kind='session'))
            pools.append(dict(name=nm+' low',typ='L',p=min(bars[i]['l'] for i in sel),t=endt,kind='session'))
    return pools
for s in INSTS:
    LEVELS[s]={}
    for di,sd in enumerate(days):
        LEVELS[s][str(sd)]={p['name']:p['p'] for p in session_pools(s,di)}
def all_pools(s):
    pools=[]
    for di,sd in enumerate(days):
        idx=SESS_IDX[s][sd]; bars=BARS[s]['5m']
        for p in session_pools(s,di):
            p.update(sd=sd,expire=bars[idx[-1]]['t']+300,tf='session'); pools.append(p)
    life={'5m':2,'15m':4,'1h':8}
    for tf in TF:
        A=ATR[s][tf]; bars=BARS[s][tf]; act=[]
        for w in SW[s][tf]:
            tol=0.15*A[w['i']]; eq=None
            act=[p for p in act if p['expire']>w['conf_t']] if len(act)>40 else act
            for p in act:
                if p['typ']==w['typ'] and abs(p['p']-w['p'])<=tol and p['expire']>w['conf_t'] and p.get('swept') is None: eq=p
            sdi=DI[bars[w['i']]['sd']]; ei=min(len(days)-1,sdi+life[tf]); exp=BARS[s]['5m'][SESS_IDX[s][days[ei]][-1]]['t']+300
            if eq:
                eq['name']=('EQH' if w['typ']=='H' else 'EQL'); eq['kind']='eq'; eq['touches']+=1; eq['expire']=exp
                continue
            p=dict(name=('BSL' if w['typ']=='H' else 'SSL'),typ=w['typ'],p=w['p'],t=w['conf_t']+TF[tf]*60,kind='swing',tf=tf,expire=exp,touches=1,src_t=w['t'],sd=bars[w['i']]['sd'])
            act.append(p); pools.append(p)
    return pools
WIN=[('London',480,660),('NY',870,1050)]
def window(m):
    sm=smin(m)
    for n,a,b in WIN:
        if a<=sm<b: return n
    return None
POOLS={}; SWEEPS={}
for s in INSTS:
    bars=BARS[s]['5m']; A=ATR[s]['5m']; pools=sorted(all_pools(s),key=lambda p:p['t']); POOLS[s]=pools
    tidx={b['t']:i for i,b in enumerate(bars)}
    sweeps=[]
    # index pools by activation
    import bisect
    starts=[p['t'] for p in pools]; active=[]; pi=0
    for i,b in enumerate(bars):
        while pi<len(pools) and pools[pi]['t']<=b['t']:
            if pools[pi]['tf']=='session' and pools[pi]['sd']!=b['sd']: pi+=1; continue
            active.append(pools[pi]); pi+=1
        keep=[]
        for p in active:
            if b['t']>=p['expire']: continue
            hit=(b['h']>p['p']) if p['typ']=='H' else (b['l']<p['p'])
            if not hit: keep.append(p); continue
            cls='acceptance'; back_t=None
            for k in range(0,3):
                if i+k>=len(bars): break
                bk=bars[i+k]
                if (p['typ']=='H' and bk['c']<p['p']) or (p['typ']=='L' and bk['c']>p['p']):
                    cls='manipulation' if k==0 else 'delayed'; back_t=bk['t']; break
            p['swept']=b['t']
            rng=b['h']-b['l']
            sw=dict(i=i,t=b['t'],pool=p,cls=cls,win=window(b['m']),ext=b['h'] if p['typ']=='H' else b['l'],leg=rng>=1.5*A[i],sd=b['sd'],back_t=back_t)
            sweeps.append(sw)
        active=keep
    SWEEPS[s]=sweeps
# SMT check
PTIMES={s:[b['t'] for b in BARS[s]['5m']] for s in INSTS}
def pair_took(s,sw):
    pr=PAIR.get(s)
    if not pr: return None
    p=sw['pool']; pb=BARS[pr]['5m']
    if p['tf']=='session':
        lv=LEVELS[pr][str(sw['sd'])].get(p['name'])
        if lv is None: return None
        start=p['t']
    else:
        # pair's extreme around the pool's source swing (±2 bars)
        st=p['src_t']; PT=PTIMES[pr]; a_=bisect.bisect_left(PT,st-600); b_=bisect.bisect_right(PT,st+600); win=pb[a_:b_]
        if not win: return None
        lv=max(b['h'] for b in win) if p['typ']=='H' else min(b['l'] for b in win)
        start=st+600
    PT=PTIMES[pr]; a_=bisect.bisect_right(PT,start); b_=bisect.bisect_right(PT,sw['t']+300); seg=pb[a_:b_]
    if not seg: return None
    took=any(b['h']>lv for b in seg) if p['typ']=='H' else any(b['l']<lv for b in seg)
    return dict(pair=pr,pair_level=lv,took=took)
for s in TRADED:
    for sw in SWEEPS[s]:
        r=pair_took(s,sw); sw['smt']=(r is not None and not r['took']); sw['pair']=r
# emit pool/sweep events
for s in TRADED:
    for p in POOLS[s]:
        if p['kind']=='swing' and p['tf']=='5m' and p.get('swept') is None: continue  # declutter unswept minor pools
        p['ev']=ev(t=p['t'],inst=s,tf=p['tf'],kind='pool_formed',p=p['p'],name=p['name'],typ=p['typ'],pk=p['kind'],t_end=p.get('swept') or p['expire'],swept=p.get('swept'),touches=p.get('touches',1))
    for sw in SWEEPS[s]:
        p=sw['pool']
        sw['ev']=ev(t=sw['t'],inst=s,tf=p['tf'],kind='sweep',p=p['p'],name=p['name'],typ=p['typ'],pk=p['kind'],cls=sw['cls'],win=sw['win'],ext=sw['ext'],smt=sw['smt'])
        if sw['leg']: ev(t=sw['t'],inst=s,tf='5m',kind='manip_leg',p=sw['ext'],q=p['p'],typ=p['typ'])
        if sw['smt']: ev(t=sw['t'],inst=s,tf=p['tf'],kind='smt',p=p['p'],name=p['name'],typ=p['typ'],pair=sw['pair']['pair'],pair_level=sw['pair']['pair_level'])
# session opens
for s in TRADED:
    bars=BARS[s]['5m']
    for i,b in enumerate(bars):
        for nm,mm in (('Asia open',20*60),('London open',2*60),('New York open',9*60+30)):
            if b['m']==mm: ev(t=b['t'],inst=s,tf='session',kind='session_open',p=b['o'],name=nm)
# ---------------- trade simulation
def walk(s,side,entry,stop,target,fill_i):
    bars=BARS[s]['5m']; risk=abs(entry-stop); d=-1 if side=='short' else 1
    mfe=0; mae=0; exit_=None
    for k in range(fill_i,len(bars)):
        b=bars[k]
        fav=(b['l'] if d==-1 else b['h']); adv=(b['h'] if d==-1 else b['l'])
        if b['sd']!=bars[fill_i]['sd'] or smin(b['m'])>=smin(15*60+55):
            r=(b['o']-entry)*d/risk; return dict(kind='time',R=r,t=b['t'],px=b['o'],mfe=mfe,mae=mae,k=k)
        hs=(adv-stop)*d<=0 if False else ((adv>=stop) if d==-1 else (adv<=stop))
        ht=((fav<=target) if d==-1 else (fav>=target)) and k>fill_i
        if hs:
            if exit_ is None: exit_=dict(kind='loss',R=-1.0,t=b['t'],px=stop,k=k)
            mae=-1.0; exit_.update(mfe=mfe,mae=mae); return exit_
        mfe=max(mfe,(fav-entry)*d/risk); mae=min(mae,(adv-entry)*d/risk)
        if ht and exit_ is None:
            exit_=dict(kind='win',R=abs(target-entry)/risk,t=b['t'],px=target,k=k)
            # continue walking to measure MFE until stop/time for counterfactuals (bounded)
        if exit_ is not None and k-exit_['k']>36:
            exit_.update(mfe=mfe,mae=mae); return exit_
    b=bars[-1]; r=(b['c']-entry)*d/risk
    if exit_ is not None: exit_.update(mfe=mfe,mae=mae); return exit_     # data ran out (e.g. today's session still going)
    return dict(kind='time',R=r,t=b['t'],px=b['c'],mfe=mfe,mae=mae,k=len(bars)-1)
K5={}
def k5_of(s):
    if s not in K5:
        t5={b['t']:i for i,b in enumerate(BARS[s]['5m'])}; T=M1[s][0]
        K5[s]=array('i',[t5.get(int(x)//300*300,-1) for x in T])
    return K5[s]
M1IDX={}
def walk1m(s,side,entry,stop,target,fill_k5):
    bars=BARS[s]['5m']; T,O,H,L,C=M1[s]; k5=k5_of(s); d=-1 if side=='short' else 1; risk=abs(entry-stop)
    if s not in M1IDX: M1IDX[s]=list(T)
    t0=bars[fill_k5]['t']; j=bisect.bisect_left(M1IDX[s],t0); sd=bars[fill_k5]['sd']
    # find the fill minute inside the 5m bar
    jf=j
    while jf<len(T) and T[jf]<t0+300:
        if (H[jf]>=entry if d==-1 else L[jf]<=entry): break
        jf+=1
    if jf>=len(T) or T[jf]>=t0+300: jf=j
    res={}; st={'none':stop,'be1':stop}; mfe=0.0; mae=0.0; first=True
    for i in range(jf,len(T)):
        kk=k5[i]
        if kk<0: continue
        b=bars[kk]
        if b['sd']!=sd or smin(b['m'])>=smin(15*60+55):
            for m in ('none','be1'):
                if m not in res: res[m]=dict(kind='time',R=(O[i]-entry)*d/risk,t=int(T[i]),px=O[i],k=kk)
            break
        fav=L[i] if d==-1 else H[i]; adv=H[i] if d==-1 else L[i]
        for m in ('none','be1'):
            if m in res: continue
            sp=st[m]
            if (adv>=sp) if d==-1 else (adv<=sp):
                res[m]=dict(kind='loss' if sp==stop else 'scratch',R=(sp-entry)*d/risk,t=int(T[i]),px=sp,k=kk); continue
            if not first and ((fav<=target) if d==-1 else (fav>=target)):
                res[m]=dict(kind='win',R=abs(target-entry)/risk,t=int(T[i]),px=target,k=kk)
        if 'none' not in res: mae=min(mae,(adv-entry)*d/risk)
        mfe=max(mfe,(fav-entry)*d/risk) if ('none' not in res or (int(T[i])-res['none']['t'])<=10800) else mfe
        if mfe>=1.0: st['be1']=entry
        first=False
        if len(res)==2 and (int(T[i])-res['none']['t'])>10800: break
    for m in ('none','be1'):
        if m not in res: res[m]=dict(kind='time',R=(C[-1]-entry)*d/risk,t=int(T[-1]),px=C[-1],k=len(bars)-1)
    w=res['none']; w['mfe']=mfe; w['mae']=max(-1.0,mae); w['be']=res['be1']; return w
KINDS_W=['time','loss','scratch','win']
def walk1m_cpp(s,side,entry,stop,tgt,fill_k5):
    f=_CPP if _CPP is not None else _load_cpp()
    if not f: return walk1m(s,side,entry,stop,tgt,fill_k5)
    cd=_cpp_inputs(s); b=BARS[s]['5m'][fill_k5]; out=(ctypes.c_double*12)()
    rc=f(*cd['args'],float(b['t']),cd['sdi'][b['sd']],-1 if side=='short' else 1,float(entry),float(stop),float(tgt),out)
    if rc!=0: return walk1m(s,side,entry,stop,tgt,fill_k5)
    mk=lambda o: dict(kind=KINDS_W[int(out[o])],R=out[o+1],t=int(out[o+2]),px=out[o+3],k=int(out[o+4]))
    w=mk(0); w['mfe']=out[10]; w['mae']=out[11]; w['be']=mk(5); return w
PSTART={}
def nearest_target(s,sd,side,entry,risk,t):
    if s not in PSTART: PSTART[s]=[p['t'] for p in POOLS[s]]
    cands=[]; PS=PSTART[s]; a_=bisect.bisect_left(PS,t-14*86400); b_=bisect.bisect_right(PS,t)
    for p in POOLS[s][a_:b_]:
        if p['t']>t or p['expire']<=t or (p.get('swept') and p['swept']<=t): continue
        if p['tf']=='session' and p['sd']!=sd: continue
        if side=='short' and p['typ']=='L' and p['p']<entry: cands.append((entry-p['p'],p))
        if side=='long' and p['typ']=='H' and p['p']>entry: cands.append((p['p']-entry,p))
    cands.sort(key=lambda x:x[0])
    for dist,p in cands:
        if dist/risk>=2.0: return p['p'],lvl_name(p)
    return (entry-2*risk if side=='short' else entry+2*risk),'2× the risk'
PN={'NQ':'Nasdaq','ES':'S&P 500','GC':'gold','SI':'silver'}
def lvl_name(p):
    n={'PDH':"yesterday's high",'PDL':"yesterday's low",'PWH':"last week's high",'PWL':"last week's low"}.get(p['name'])
    if n: return n
    if p['kind']=='session': return p['name']
    if p['kind']=='eq': return f"equal {'highs' if p['typ']=='H' else 'lows'} ({p['tf']}, touched {p.get('touches',2)} times)"
    return f"a {p['tf']} {'high' if p['typ']=='H' else 'low'}"
TRADES=[]
POOLQ={'session':25,'eq':20,'1h':22,'15m':15,'5m':5}
def pool_quality(p): return POOLQ['session'] if p['tf']=='session' else (POOLQ['eq'] if p['kind']=='eq' else POOLQ[p['tf']])
def simulate(s,sw,m,d,side,z,tmode):
    bars=BARS[s]['5m']; tidx={}
    seg=bars[sw['i']:m['i']+1]
    ext=max(b['h'] for b in seg) if d==-1 else min(b['l'] for b in seg)
    entry=z['bot'] if d==-1 else z['top']; entry=round(entry/TICK[s])*TICK[s]
    stop=ext+BUF[s] if d==-1 else ext-BUF[s]; risk=abs(entry-stop)
    if risk<=0 or (entry-stop)*d<=0: return None
    if tmode=='pool': tgt,tname=nearest_target(s,sw['sd'],side,entry,risk,m['t'])
    else:
        k=float(tmode[:-1]); tgt=entry-k*risk if d==-1 else entry+k*risk; tname=f"{tmode[:-1]}× the risk"
    fill=None; status='cancelled'
    for k in range(m['i']+1,min(m['i']+13,len(bars))):
        bk=bars[k]
        if bk['sd']!=sw['sd']: break
        if ((bk['l']<=tgt) if d==-1 else (bk['h']>=tgt)): status='missed'; break
        if ((bk['h']>=entry) if d==-1 else (bk['l']<=entry)): fill=k; break
    sim=dict(zone=z['kind'],entry=entry,stop=round(stop,4),target=round(tgt,4),tname=tname,risk=risk,rr=abs(tgt-entry)/risk,ext=ext,status=status,fill=fill)
    if fill is not None:
        w=walk1m_cpp(s,side,entry,stop,tgt,fill)
        sim.update(status=w['kind'],R=round(w['R'],2),fill_t=bars[fill]['t'],exit_t=w['t'],exit=round(w['px'],4),mfe=round(w['mfe'],2),mae=round(w['mae'],2),bars=w['k']-fill+1,exit_k=w['k'],fill_bars=fill-m['i'],R_be=round(w['be']['R'],2),exit_k_be=w['be']['k'])
    return sim
BRKT={s:[o['t'] for o in BRK[s]['5m']] for s in TRADED}
Z5={s:sorted([z for z in ZONES[s] if z['tf']=='5m'],key=lambda z:z['t']) for s in TRADED}; Z5T={s:[z['t'] for z in Z5[s]] for s in TRADED}
CANDS=[]   # every window sweep on a traded market, with every entry/target sim it could have had
for s in TRADED:
    bars=BARS[s]['5m']; A=ATR[s]['5m']; brk5=BRK[s]['5m']
    for sw in SWEEPS[s]:
        if sw['win'] is None: continue
        p=sw['pool']; side='short' if p['typ']=='H' else 'long'; d=-1 if side=='short' else 1
        st={}
        st['1']=[(p['tf']!='5m' or p['kind']=='eq'),lvl_name(p)+('' if (p['tf']!='5m' or p['kind']=='eq') else ': only a minor level')]
        st['2']=[sw['cls']!='acceptance',{'manipulation':'came straight back','delayed':'came back within 10 min','acceptance':'price stayed past it: a breakout, not a trap'}[sw['cls']]+f", {sw['win']} session"]
        pr=sw['pair']
        st['3']=[bool(sw['smt']),(f"{PN[pr['pair']]} {'also went past' if pr['took'] else 'did not go past'} its matching level ({pr['pair_level']:,.2f})" if pr else 'no data for the other market')]
        m=None
        j0=bisect.bisect_right(BRKT[s],sw['t'])
        for o in brk5[j0:j0+40]:
            if o['t']>sw['t']+40*60: break
            if sw['t']<o['t']<=sw['t']+40*60 and o['t']>=(sw['back_t'] or 0) and o['dir']==d and o['typ'] in('mss','choch'): m=o; break
        st['4']=[bool(m and m['disp']),(f"trend flipped at {dt.datetime.fromtimestamp(m['t'],NY):%H:%M}"+(' with a big candle' if m['disp'] else ', but without a big candle') if m else 'no trend flip within 40 min')]
        sims={}
        if m:
            a_=bisect.bisect_left(Z5T[s],sw['t']); b_=bisect.bisect_right(Z5T[s],m['t']+300); zs=[z for z in Z5[s][a_:b_] if z['dir']==d and z['i']<=m['i']]
            for kind in ('fvg','ob'):
                zk=sorted([z for z in zs if z['kind']==kind],key=lambda z:-z['t'])
                if zk:
                    for tm in ('pool','2R','3R'): sims[(kind,tm)]=simulate(s,sw,m,d,side,zk[0],tm)
        htf=trend_at(s,'1h',sw['t']); lv=LEVELS[s][str(sw['sd'])]
        eqm=((lv['PDH']+lv['PDL'])/2) if 'PDH' in lv else None
        disp=0
        if m:
            mb=bars[m['i']]; disp=min(20,round(20*((mb['h']-mb['l'])/A[m['i']])/2.5))
        CANDS.append(dict(s=s,sw=sw,p=p,side=side,d=d,st=st,m=m,sims=sims,h1=(htf==d),eqm=eqm,disp=disp,sd=str(sw['sd']),dow=bars[sw['i']]['dow'],hour=bars[sw['i']]['m']//60))
OBC=[]
for s in TRADED:
    bars=BARS[s]['5m']
    for z in sorted([z for z in ZONES[s] if z['kind']=='ob' and z['tf']=='15m' and z['mit']],key=lambda z:z['brk_t']):
        bt=z['brk_t']; start=bisect.bisect_left(PTIMES[s],bt+900)
        if start>=len(bars): continue
        d=z['dir']; side='long' if d==1 else 'short'; k0=None
        for k in range(start,min(start+12*24,len(bars))):
            b=bars[k]
            if (d==1 and b['l']<=z['top']) or (d==-1 and b['h']>=z['bot']): k0=k; break
        if k0 is None: continue
        b=bars[k0]; win=window(b['m']); htf=trend_at(s,'1h',b['t'])
        entry=z['top'] if d==1 else z['bot']; stop=(z['bot']-BUF[s]) if d==1 else (z['top']+BUF[s]); risk=abs(entry-stop)
        if risk<=0: continue
        tgt,tname=nearest_target(s,b['sd'],side,entry,risk,b['t'])
        w=walk1m_cpp(s,side,entry,stop,tgt,k0)
        OBC.append(dict(s=s,sd=str(b['sd']),win=win,side=side,d=d,h1=(htf==d),htf=htf,entry=entry,stop=stop,target=tgt,tname=tname,rr=abs(tgt-entry)/risk,fill_t=b['t'],t=b['t'],k0=k0,w=w,dow=b['dow'],hour=b['m']//60))
