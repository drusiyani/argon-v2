import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import json, datetime as dt, urllib.request, hashlib, collections
from zoneinfo import ZoneInfo
NY=ZoneInfo("America/New_York")
INSTS=['NQ','ES','YM','RTY']; TRADED=['NQ','ES','YM','RTY']; PAIR={'NQ':'ES','ES':'NQ','YM':'ES','RTY':'ES'}
TICK={'NQ':0.25,'ES':0.25,'YM':1.0,'RTY':0.1}; BUF={'NQ':2.0,'ES':0.75,'YM':8.0,'RTY':0.5}
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
B5={s:load(s,os.path.join(ROOT,'data','futures',f'{s}F.json')) for s in INSTS}
B2={s:load(s,os.path.join(ROOT,'data','futures',f'{s}F2.json')) for s in ['NQ','ES','YM','RTY']}
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
def ev(**k): EV.append(k); return len(EV)-1
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
for s in TRADED:
    bars=BARS[s]['5m']; sw=SW[s]['5m']
    for o in BRK[s]['5m']:
        cand=[w for w in sw if w['t']>o['t'] and w['typ']==('L' if o['dir']==1 else 'H')][:1]
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
def session_pools(s,di):
    sd=days[di]; idx=SESS_IDX[s][sd]; bars=BARS[s]['5m']; pools=[]
    if di>0:
        pidx=SESS_IDX[s][days[di-1]]
        pools.append(dict(name='PDH',typ='H',p=max(bars[i]['h'] for i in pidx),t=bars[idx[0]]['t'],kind='session'))
        pools.append(dict(name='PDL',typ='L',p=min(bars[i]['l'] for i in pidx),t=bars[idx[0]]['t'],kind='session'))
    # previous week
    wk=sd.isocalendar()[1]; prev=[d for d in days if d.isocalendar()[1]==wk-1]
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
            for p in act:
                if p['typ']==w['typ'] and abs(p['p']-w['p'])<=tol and p['expire']>w['conf_t'] and p.get('swept') is None: eq=p
            sdi=days.index(bars[w['i']]['sd']); ei=min(len(days)-1,sdi+life[tf]); exp=BARS[s]['5m'][SESS_IDX[s][days[ei]][-1]]['t']+300
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
        st=p['src_t']; win=[b for b in pb if abs(b['t']-st)<=600]
        if not win: return None
        lv=max(b['h'] for b in win) if p['typ']=='H' else min(b['l'] for b in win)
        start=st+600
    seg=[b for b in pb if start<b['t']<=sw['t']+300]  # allow same bar
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
def walk_be(s,side,entry,stop,target,fill_i):
    bars=BARS[s]['5m']; risk=abs(entry-stop); d=-1 if side=='short' else 1; st=stop; mfe=0
    for k in range(fill_i,len(bars)):
        b=bars[k]
        if b['sd']!=bars[fill_i]['sd'] or smin(b['m'])>=smin(15*60+55): return dict(R=(b['o']-entry)*d/risk,k=k)
        fav=(b['l'] if d==-1 else b['h']); adv=(b['h'] if d==-1 else b['l'])
        if (adv>=st) if d==-1 else (adv<=st): return dict(R=(st-entry)*d/risk,k=k)
        if k>fill_i and ((fav<=target) if d==-1 else (fav>=target)): return dict(R=abs(target-entry)/risk,k=k)
        mfe=max(mfe,(fav-entry)*d/risk)
        if mfe>=1: st=entry
    return dict(R=(bars[-1]['c']-entry)*d/risk,k=len(bars)-1)
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
def nearest_target(s,sd,side,entry,risk,t):
    cands=[]
    for p in POOLS[s]:
        if p['t']>t or p['expire']<=t or (p.get('swept') and p['swept']<=t): continue
        if p['tf']=='session' and p['sd']!=sd: continue
        if side=='short' and p['typ']=='L' and p['p']<entry: cands.append((entry-p['p'],p))
        if side=='long' and p['typ']=='H' and p['p']>entry: cands.append((p['p']-entry,p))
    cands.sort(key=lambda x:x[0])
    for dist,p in cands:
        if dist/risk>=2.0: return p['p'],lvl_name(p)
    return (entry-2*risk if side=='short' else entry+2*risk),'2× the risk'
PN={'NQ':'Nasdaq','ES':'S&P 500','YM':'Dow','RTY':'Russell 2000'}
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
        w=walk(s,side,entry,stop,tgt,fill)
        sim.update(status=w['kind'],R=round(w['R'],2),fill_t=bars[fill]['t'],exit_t=w['t'],exit=round(w['px'],4),mfe=round(w['mfe'],2),mae=round(w['mae'],2),bars=w['k']-fill+1,exit_k=w['k'],fill_bars=fill-m['i'])
        wb=walk_be(s,side,entry,stop,tgt,fill); sim.update(R_be=round(wb['R'],2),exit_k_be=wb['k'])
    return sim
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
        for o in brk5:
            if sw['t']<o['t']<=sw['t']+40*60 and o['t']>=(sw['back_t'] or 0) and o['dir']==d and o['typ'] in('mss','choch'): m=o; break
        st['4']=[bool(m and m['disp']),(f"trend flipped at {dt.datetime.fromtimestamp(m['t'],NY):%H:%M}"+(' with a big candle' if m['disp'] else ', but without a big candle') if m else 'no trend flip within 40 min')]
        sims={}
        if m:
            zs=[z for z in ZONES[s] if z['tf']=='5m' and z['dir']==d and sw['t']<=z['t'] and z['i']<=m['i']]
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
        bt=z['brk_t']; start=next((i for i,b in enumerate(bars) if b['t']>=bt+900),None)
        if start is None: continue
        d=z['dir']; side='long' if d==1 else 'short'; k0=None
        for k in range(start,min(start+12*24,len(bars))):
            b=bars[k]
            if (d==1 and b['l']<=z['top']) or (d==-1 and b['h']>=z['bot']): k0=k; break
        if k0 is None: continue
        b=bars[k0]; win=window(b['m']); htf=trend_at(s,'1h',b['t'])
        entry=z['top'] if d==1 else z['bot']; stop=(z['bot']-BUF[s]) if d==1 else (z['top']+BUF[s]); risk=abs(entry-stop)
        if risk<=0: continue
        tgt,tname=nearest_target(s,b['sd'],side,entry,risk,b['t'])
        w=walk(s,side,entry,stop,tgt,k0)
        OBC.append(dict(s=s,sd=str(b['sd']),win=win,side=side,d=d,h1=(htf==d),htf=htf,entry=entry,stop=stop,target=tgt,tname=tname,rr=abs(tgt-entry)/risk,fill_t=b['t'],t=b['t'],k0=k0,w=w,dow=b['dow'],hour=b['m']//60))
# ---------------- rules: v0.2 baseline and the dial space the lab searches
BASE=dict(name='v0.2 baseline',entry='fvg_first',windows='both',bias='none',smt='required',pool='quality',markets='all',target='pool',risk=False)
RISK=dict(min_rr=1.5,max_entries=5,day_loss=-2.0)
MK={'all':('NQ','ES','YM','RTY'),'nq':('NQ',),'nq_es':('NQ','ES'),'es':('ES',),'gc':('ES',)}
DAILY={}
for _s in TRADED:
    _b=BARS[_s]['5m']
    for _di,_sd in enumerate(days):
        if _di==0: continue
        _pi=SESS_IDX[_s][days[_di-1]]
        if _pi: DAILY[(_s,str(_sd))]=1 if _b[_pi[-1]]['c']>_b[_pi[0]]['o'] else -1
def nyopen(c): return c['sw']['win']=='NY' and 870<=smin(BARS[c['s']]['5m'][c['sw']['i']]['m'])<960
def pick_sim(c,r):
    order={'fvg_first':('fvg','ob'),'ob_first':('ob','fvg'),'ob_only':('ob',)}[r['entry']]
    for kd in order:
        sm=c['sims'].get((kd,r['target']))
        if sm is not None: return sm
    return None
def apply_rules(r,with_records=False):
    out=[]; busy={}; day_n=collections.Counter(); day_loss=collections.defaultdict(list)
    for c in sorted(CANDS,key=lambda c:c['sw']['t']):
        fail=[]; 
        if c['s'] not in MK[r['markets']]: fail.append('M')
        if r['windows']=='ny_open':
            if not nyopen(c): fail.append('W')
        elif r['windows']!='both' and c['sw']['win']!={'ny':'NY','london':'London'}[r['windows']]: fail.append('W')
        _pk=c['p']['kind']; _tf=c['p']['tf']; _pl=r['pool']
        if (_pl=='quality' and not c['st']['1'][0]) or (_pl=='session' and _pk!='session') or (_pl=='eq' and _pk!='eq') or (_pl=='htf' and not (_pk=='session' or _tf in ('15m','1h'))): fail.append('1')
        if r.get('sweep')=='instant' and c['sw']['cls']!='manipulation': fail.append('2')
        if not c['st']['2'][0]: fail.append('2')
        sm=pick_sim(c,r) if c['m'] and c['m']['disp'] else None
        pd_ok=bool(c['eqm'] and sm and ((sm['entry']>c['eqm']) if c['d']==-1 else (sm['entry']<c['eqm'])))
        if r['bias']=='h1' and not c['h1']: fail.append('B')
        if r['bias']=='pd' and not pd_ok: fail.append('B')
        if r['bias']=='h1_pd' and not (c['h1'] and pd_ok): fail.append('B')
        if r['bias']=='daily' and DAILY.get((c['s'],c['sd']),0)!=c['d']: fail.append('B')
        if r['smt']=='required' and not c['st']['3'][0]: fail.append('3')
        if not c['st']['4'][0]: fail.append('4')
        if not sm or sm['fill'] is None: fail.append('5')
        risk_why=None
        if not fail and r.get('risk',True):
            day=c['sd']
            if sm['rr']<RISK['min_rr']: risk_why=f"target only worth {sm['rr']:.1f}× the risk (needs {RISK['min_rr']}×)"
            elif day_n[day]>=RISK['max_entries']: risk_why=f"already {RISK['max_entries']} trades today"
            elif sum(R for (xt,R) in day_loss[day] if xt<=sm['fill_t'])<=RISK['day_loss']: risk_why=f"already lost {-RISK['day_loss']:.0f}R today"
            if risk_why: fail.append('R')
        if not fail and sm['fill']<=busy.get(c['s'],-1): fail.append('P')
        fired=not fail
        if fired and r.get('manage')=='be1' and 'R_be' in sm:
            sm=dict(sm,R=sm['R_be'],exit_k=sm['exit_k_be'],status='win' if sm['R_be']>0 else 'scratch' if sm['R_be']==0 else sm['status'])
        if fired:
            busy[c['s']]=sm['exit_k']; day_n[c['sd']]+=1; day_loss[c['sd']].append((sm['exit_t'],sm['R']))
        if with_records or fired: out.append(dict(c=c,sm=sm,fired=fired,fail=fail,pd=pd_ok,risk_why=risk_why))
    return out
def apply_ob(r,with_records=False):
    out=[]; busy={}
    for c in sorted(OBC,key=lambda c:c['t']):
        fail=[]
        if c['s'] not in MK[r['markets']]: fail.append('M')
        if c['win'] is None or (r['windows']=='ny_open' and not (c['win']=='NY' and c['hour']<10)) or (r['windows'] not in ('both','ny_open') and c['win']!={'ny':'NY','london':'London'}[r['windows']]): fail.append('W')
        if not c['h1']: fail.append('T')
        if r.get('risk',True) and c['rr']<RISK['min_rr']: fail.append('R')
        if not fail and c['k0']<=busy.get(c['s'],-1): fail.append('P')
        fired=not fail
        if fired: busy[c['s']]=c['w']['k']
        if with_records or fired: out.append(dict(c=c,fired=fired,fail=fail))
    return out
def metrics(Rs):
    n=len(Rs); net=[x-0.05 for x in Rs]; eq=0; pk=0; dd=0
    for x in net: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    return dict(n=n,net=round(sum(net),2),wr=round(sum(1 for x in Rs if x>0)/n,3) if n else 0,avg=round(sum(net)/n,3) if n else 0,dd=round(dd,2))
TUNE_END='2026-09-18'; HALF='2026-08-26'
def split(trs,getsd,getR):
    a=[getR(t) for t in trs if getsd(t)<=HALF]; b=[getR(t) for t in trs if HALF<getsd(t)<=TUNE_END]; c=[getR(t) for t in trs if getsd(t)>TUNE_END]
    return metrics(a),metrics(b),metrics(a+b),metrics(c)
import random, itertools
random.seed(7)
def mc_dd(Rs,n=2000):
    if len(Rs)<5: return None
    dds=[]
    for _ in range(n):
        x=Rs[:]; random.shuffle(x); eq=pk=dd=0
        for r in x: eq+=r-0.05; pk=max(pk,eq); dd=min(dd,eq-pk)
        dds.append(dd)
    dds.sort(); return round(dds[int(0.05*n)],2)
GATE=dict(min_tune=20,min_sealed=8,mc_dd=-12.0)
LAB=[]
DIALS=dict(entry=['fvg_first','ob_first','ob_only'],windows=['both','ny','london'],bias=['none','h1','pd','h1_pd'],smt=['required','optional'],pool=['quality','any'],markets=['all','nq','nq_es'],target=['pool','2R','3R'])
if os.environ.get('FARM_LIGHT'): DIALS={k:v[:1] for k,v in DIALS.items()}   # quick mode for the live desk
for combo in itertools.product(*DIALS.values()):
    r=dict(zip(DIALS.keys(),combo)); r['risk']=True
    tr=apply_rules(r); a,b,ab,c=split(tr,lambda t:t['c']['sd'],lambda t:t['sm']['R'])
    LAB.append(dict(route='chain',rules=r,A=a,B=b,tune=ab,sealed=c,trades=[(t['c']['sd'],t['sm']['R']) for t in tr]))
for combo in itertools.product(['all','nq','nq_es'],['both','ny','london']):
    r=dict(markets=combo[0],windows=combo[1],risk=True)
    tr=apply_ob(r); a,b,ab,c=split(tr,lambda t:t['c']['sd'],lambda t:t['c']['w']['R'])
    LAB.append(dict(route='ob',rules=r,A=a,B=b,tune=ab,sealed=c,trades=[(t['c']['sd'],t['c']['w']['R']) for t in tr]))
# baseline v0.2 (as it was: no risk engine, no extra gates)
bt=apply_rules(BASE); a,b,ab,c=split(bt,lambda t:t['c']['sd'],lambda t:t['sm']['R'])
BASEL=dict(route='chain',rules=BASE,A=a,B=b,tune=ab,sealed=c,trades=[(t['c']['sd'],t['sm']['R']) for t in bt],baseline=True)
# gate stage 1: tuning only (walk-forward halves both positive)
for L in LAB:
    L['stage1']=L['tune']['n']>=GATE['min_tune'] and L['A']['net']>0 and L['B']['net']>0
cand=[L for L in LAB if L['stage1']]
cand.sort(key=lambda L:-L['tune']['avg'])
finalists=cand[:5]
for L in LAB: L['status']='failed walk-forward' if not L['stage1'] else 'not shortlisted'
for L in finalists:
    L['mc']=mc_dd([R for _,R in L['trades'] if _<=TUNE_END])
    ok=L['sealed']['n']>=GATE['min_sealed'] and L['sealed']['net']>0 and (L['mc'] is not None and L['mc']>GATE['mc_dd'])
    L['status']='passed' if ok else 'failed sealed test'
passed=[L for L in finalists if L['status']=='passed']
LIVE_CHAIN=next((L for L in passed if L['route']=='chain'),None)
LIVE_OB=next((L for L in passed if L['route']=='ob'),None)
# dial importance ("which inputs actually help"): mean tuning avg net R per dial value, chain variants with n>=10
IMP={}
for dk,vals in DIALS.items():
    IMP[dk]={}
    for v in vals:
        xs=[L['tune']['avg'] for L in LAB if L['route']=='chain' and L['rules'][dk]==v and L['tune']['n']>=10]
        IMP[dk][v]=(round(sum(xs)/len(xs),3),len(xs)) if xs else (None,0)
BT=json.load(open(os.path.join(ROOT,'data','bt_out.json')))
V03=dict(BT['now']['chain']['rules'],risk=True,name='v0.10') if BT['now']['chain'] else dict(BASE,risk=True,name='v0.4')
V03OB=dict(BT['now']['ob']['rules'],risk=True) if BT['now']['ob'] else dict(markets='all',windows='both',risk=True)
print('variants',len(LAB),'stage1',len(cand),'passed',[(L['route'],L['rules'],L['tune'],L['sealed'],L['mc']) for L in passed])
print('finalists',[(L['route'],L['rules'],L['tune']['net'],L['sealed'],L.get('mc'),L['status']) for L in finalists])
print('baseline',BASEL['tune'],BASEL['sealed'])
for L in []:
    if L['route']=='ob': print('OB',L['rules'],L['A']['net'],L['B']['net'],L['tune'],L['sealed']['n'],L['sealed']['net'],L['status'])
# ---------------- build farm records from the live rules
STEPNAMES={'M':'market not on the list','W':'outside trading hours','B':'against the day\'s direction','P':'already in a trade on this market','T':'hourly trend against it','R':'risk rules'}
recs=apply_rules(V03,with_records=True)
for x in recs:
    c=x['c']; sw=c['sw']; p=c['p']; sm=x['sm']; s=c['s']
    steps={k:[1 if v[0] else 0,v[1]] for k,v in c['st'].items()}
    steps['5']=[1 if (sm and sm['fill'] is not None) else 0,('no gap or order block was left to enter at' if not sm else (f"price came back to the {'order block' if sm['zone']=='ob' else 'gap'} at {sm['entry']:,.2f}" if sm['fill'] is not None else ('price went straight to the target without coming back' if sm['status']=='missed' else 'price didn\'t come back within an hour'))) if c['m'] else 'never got this far']
    biasok=('B' not in x['fail'])
    steps['B']=[1 if biasok else 0,{'none':'rule switched off for now','h1':'hourly trend '+('agreed' if c['h1'] else 'disagreed'),'pd':('right' if x['pd'] else 'wrong')+' half of yesterday\'s range','h1_pd':'hourly trend '+('agreed' if c['h1'] else 'disagreed')+', '+('right' if x['pd'] else 'wrong')+' half of the range','daily':('same' if DAILY.get((s,c['sd']),0)==c['d'] else 'opposite')+' direction to yesterday'}[V03['bias']]]
    steps['R']=[0 if 'R' in x['fail'] else 1,x['risk_why'] or (f"target worth {sm['rr']:.1f}× the risk" if sm else 'not checked')]
    fail=[f for f in x['fail'] if f!='M' or True]
    pq=pool_quality(p)
    score=pq+(15 if sw['smt'] else 0)+c['disp']+(15 if c['h1'] else 0)+(10 if x['pd'] else 0)+(10 if sw['win']=='NY' else 6)
    score=min(100,score); grade='A++' if score>=85 else 'A+' if score>=72 else 'A' if score>=60 else 'B' if score>=45 else 'C'
    rec=dict(id=f"{s}-{sw['sd']}-{len(TRADES):04d}",route='chain',inst=s,sd=c['sd'],win=sw['win'],side=c['side'],pool=p['name'],pool_tf=p['tf'],pool_kind=p['kind'],pool_p=p['p'],sweep_t=sw['t'],sweep_cls=sw['cls'],smt=sw['smt'],pair=(sw['pair']['pair'] if sw['pair'] else None),steps=steps,failed=fail,fired=x['fired'],score=score,grade=grade,bias=c['h1'],pd=x['pd'],disp=c['disp'],dow=c['dow'],hour=c['hour'])
    if sm:
        rec.update(entry=sm['entry'],stop=sm['stop'],target=sm['target'],tname=sm['tname'],zone=sm['zone'],overlap=False,mss_t=c['m']['t'],status=sm['status'])
        if sm['fill'] is not None:
            rec.update(fill_t=sm['fill_t'],R=sm['R'],Rnet=round(sm['R']-0.05,2),exit_t=sm['exit_t'],exit=sm['exit'],mfe=sm['mfe'],mae=sm['mae'],bars=sm['bars'],fill_bars=sm['fill_bars'])
    TRADES.append(rec)
    if x['fired']:
        ev(t=rec['fill_t'],inst=s,tf='5m',kind='fire',p=rec['entry'],trade=rec['id'],route='chain',grade=grade)
        ev(t=rec['exit_t'],inst=s,tf='5m',kind='outcome',p=rec['exit'],trade=rec['id'],R=rec['R'],res=rec['status'])
    elif 'M' not in fail and 'W' not in fail:
        ev(t=sw['t'],inst=s,tf='5m',kind='refusal',p=p['p'],trade=rec['id'],step=fail[0],why=(steps.get(fail[0],[0,STEPNAMES.get(fail[0],'')])[1]))
ENABLE_OB=False   # v0.9: the order-block strategy was dropped (lost money on 5 years of real futures)
for x in (apply_ob(V03OB,with_records=True) if ENABLE_OB else []):
    c=x['c']; s=c['s']; w=c['w']
    if 'M' in x['fail'] or c['win'] is None: continue
    steps={'trend':[1 if c['h1'] else 0,f"hourly trend {'up' if c['htf']==1 else 'down' if c['htf']==-1 else 'flat'}"],'window':[1 if 'W' not in x['fail'] else 0,f"price came back at {dt.datetime.fromtimestamp(c['t'],NY):%H:%M}, {c['win']} session"],'R':[0 if 'R' in x['fail'] else 1,f"target worth {c['rr']:.1f}× the risk"]}
    rec=dict(id=f"{s}-{c['sd']}-B{len(TRADES):04d}",route='ob',inst=s,sd=c['sd'],win=c['win'],side=c['side'],pool='15m OB',pool_tf='15m',pool_kind='ob',sweep_t=c['t'],entry=round(c['entry'],4),stop=round(c['stop'],4),target=round(c['target'],4),tname=c['tname'],zone='ob',fill_t=c['t'],fired=x['fired'],failed=x['fail'],dow=c['dow'],hour=c['hour'],steps=steps,grade='B',score=50,bias=c['h1'],smt=None,status=w['kind'],R=round(w['R'],2),Rnet=round(w['R']-0.05,2),exit_t=w['t'],exit=round(w['px'],4),mfe=round(w['mfe'],2),mae=round(w['mae'],2),bars=w['k']-c['k0']+1)
    TRADES.append(rec)
    if x['fired']:
        ev(t=c['t'],inst=s,tf='15m',kind='ob_entry',p=rec['entry'],trade=rec['id'],route='ob')
        ev(t=w['t'],inst=s,tf='5m',kind='outcome',p=rec['exit'],trade=rec['id'],R=rec['R'],res=rec['status'],route='ob')
# ---------------- the desk: every setup the AI agents get to judge, and the busier rules-only rival
FEED_RULES=dict(entry='ob_first',windows='both',bias='none',smt='optional',pool='any',markets='all',target='2R',sweep='any',risk=False)
BUSY_RULES=dict(entry='ob_first',windows='both',bias='none',smt='optional',pool='any',markets='all',target='2R',sweep='instant',risk=True)
def desk_rec(x,route,fired):
    c=x['c']; sw=c['sw']; p=c['p']; sm=x['sm']; s=c['s']
    pq=pool_quality(p); score=min(100,pq+(15 if sw['smt'] else 0)+c['disp']+(15 if c['h1'] else 0)+(10 if x['pd'] else 0)+(10 if sw['win']=='NY' else 6))
    grade='A++' if score>=85 else 'A+' if score>=72 else 'A' if score>=60 else 'B' if score>=45 else 'C'
    steps={k:[1 if v[0] else 0,v[1]] for k,v in c['st'].items()}
    steps['5']=[1,f"price came back to the {'order block' if sm['zone']=='ob' else 'gap'} at {sm['entry']:,.2f}"]
    steps['B']=[1,'hourly trend '+('agreed' if c['h1'] else 'disagreed')]; steps['R']=[1,f"target worth {sm['rr']:.1f}× the risk"]
    return dict(id=f"{s}-{c['sd']}-{route[0].upper()}{len(TRADES):04d}",route=route,inst=s,sd=c['sd'],win=sw['win'],side=c['side'],pool=p['name'],pool_tf=p['tf'],pool_kind=p['kind'],pool_p=p['p'],sweep_t=sw['t'],sweep_cls=sw['cls'],smt=sw['smt'],pair=(sw['pair']['pair'] if sw['pair'] else None),steps=steps,failed=[],fired=fired,score=score,grade=grade,bias=c['h1'],pd=x['pd'],disp=c['disp'],dow=c['dow'],hour=c['hour'],
        entry=sm['entry'],stop=sm['stop'],target=sm['target'],tname=sm['tname'],zone=sm['zone'],overlap=False,mss_t=c['m']['t'],status=sm['status'],fill_t=sm['fill_t'],R=sm['R'],Rnet=round(sm['R']-0.05,2),exit_t=sm['exit_t'],exit=sm['exit'],mfe=sm['mfe'],mae=sm['mae'],bars=sm['bars'],fill_bars=sm['fill_bars'],lvl=lvl_name(p),key=f"{s}-{sw['t']}")
nfeed=nbusy=0
for x in apply_rules(FEED_RULES,with_records=True):
    if x['sm'] and x['sm']['fill'] is not None and set(x['fail'])<={'P'}:
        TRADES.append(desk_rec(x,'feed',False)); nfeed+=1
for x in apply_rules(BUSY_RULES):
    if x['fired']: TRADES.append(desk_rec(x,'busy',True)); nbusy+=1
print('desk feed setups',nfeed,'busy rival trades',nbusy)
# ---------------- opening-range breakout (Zarattini & Aziz), settings re-picked monthly by engine/extra.py
_op=os.path.join(ROOT,'data','orb_out.json'); ORB=json.load(open(_op)) if os.path.exists(_op) else None
ORBCOST={'NQ':0.75,'ES':0.5,'YM':3.0,'RTY':0.3}
norb=0
ORB_MARKETS=('NQ',)   # v0.10: Nasdaq only (the S&P version was too weak on 5 years of real futures)
for s in ORB_MARKETS:
    pick=(ORB['markets'].get(s) or ORB['markets']['both'])['now'] if ORB else {'orm':5,'stop':'candle','target':'10R'}
    bars=BARS[s]['5m']; rth={}
    for i,b in enumerate(bars):
        if 570<=b['m']<960: rth.setdefault(b['sd'],[]).append(i)
    dates=sorted(rth); rng={d:max(bars[i]['h'] for i in rth[d])-min(bars[i]['l'] for i in rth[d]) for d in dates}
    for di,d in enumerate(dates):
        idx=rth[d]; k=pick['orm']//5
        if not idx or bars[idx[0]]['m']!=570 or len(idx)<60 or len(idx)<=k: continue
        first=[bars[i] for i in idx[:k]]; o,c=first[0]['o'],first[-1]['c']; h=max(x['h'] for x in first); l=min(x['l'] for x in first)
        if h<=l or abs(c-o)<0.05*(h-l): continue
        side=1 if c>o else -1; eb=bars[idx[k]]; entry=eb['o']
        if pick.get('filter')=='trend20':   # only trade with the 20-day trend
            prevc=[bars[rth[x][-1]]['c'] for x in dates[max(0,di-20):di]]
            if len(prevc)<20 or (side==1)!=(prevc[-1]>sum(prevc)/len(prevc)): continue
        if pick['stop']=='candle': stop=l if side==1 else h
        else:
            prev=[rng[x] for x in dates[max(0,di-14):di]]
            if not prev: continue
            stop=entry-side*0.10*sum(prev)/len(prev)
        risk=(entry-stop)*side
        if risk<=0: continue
        target=entry+side*10*risk if pick['target']=='10R' else None
        ex=None; mfe=mae=0.0
        for j in idx[k:]:
            b=bars[j]; fav=(b['h']-entry)*side if side==1 else (entry-b['l']); adv=(b['l']-entry) if side==1 else (entry-b['h'])
            if (b['l']<=stop) if side==1 else (b['h']>=stop): ex=('loss',stop,b['t']); break
            if target is not None and ((b['h']>=target) if side==1 else (b['l']<=target)): ex=('win',target,b['t']); break
            mfe=max(mfe,fav/risk); mae=min(mae,adv/risk)
            if b['m']>=955: ex=('time',b['c'],b['t']); break
        if not ex: b=bars[idx[-1]]; ex=('time',b['c'],b['t'])
        Rr=round((ex[1]-entry)*side/risk-ORBCOST[s]/risk,2)
        TRADES.append(dict(id=f"{s}-{d}-O{len(TRADES):04d}",route='orb',inst=s,sd=str(d),win='NY',side='long' if side==1 else 'short',pool='opening range',pool_tf=f"{pick['orm']}m",pool_kind='orb',sweep_t=bars[idx[0]]['t'],
            entry=round(entry,4),stop=round(stop,4),target=round(target if target is not None else entry+side*10*risk,4),tname='10× the risk' if target is not None else 'the close',zone='orb',fill_t=eb['t'],exit_t=ex[2],exit=round(ex[1],4),
            R=Rr,Rnet=Rr,status=ex[0] if not (ex[0]=='time' and Rr>0) else 'time',mfe=round(mfe,2),mae=round(max(-1,mae),2),bars=0,fired=True,failed=[],dow=bars[idx[0]]['dow'],hour=9,score=50,grade='B',bias=None,smt=None,
            steps={'range':[1,f"the first {pick['orm']} minutes of the US session went {'up' if side==1 else 'down'}"+(', with the 20-day trend' if pick.get('filter')=='trend20' else '')],'stop':[1,('stop at the other side of the opening range' if pick['stop']=='candle' else 'stop a tenth of a normal day\'s range away')],'R':[1,f"cost of trading taken off: {ORBCOST[s]} points"]}))
        norb+=1
print('opening-range trades',norb)
# lab export
def lab_row(L,curve=False):
    o=dict(route=L['route'],rules={k:v for k,v in L['rules'].items() if k!='name'},A=L['A'],B=L['B'],tune=L['tune'],sealed=L['sealed'],status=L.get('status','baseline'),mc=L.get('mc'))
    if curve: o['curve']=[[sd,round(R,2)] for sd,R in L['trades']]
    return o
top=sorted([L for L in LAB if L['route']=='chain'],key=lambda L:-L['tune']['avg'] if L['tune']['n']>=10 else 99)[:30]
LABOUT=dict(gate=GATE,risk=RISK,tune_end=TUNE_END,half=HALF,dials=DIALS,n_variants=len(LAB),n_stage1=len(cand),
  baseline=lab_row(BASEL,True),stage1=[lab_row(L,True) for L in cand],finalists=[lab_row(L,True) for L in finalists],top=[lab_row(L) for L in top],ob=[lab_row(L,True) for L in LAB if L['route']=='ob'],
  live_chain=lab_row(LIVE_CHAIN,True) if LIVE_CHAIN else None,live_ob=lab_row(LIVE_OB,True) if LIVE_OB else None,importance=IMP,v03=V03,v03ob=V03OB)
RULES_VERSION='0.10'; SIG=hashlib.sha1(('argon-v2-rules-0.10-'+json.dumps(V03,sort_keys=True)).encode()).hexdigest()[:8]

# ---------------- pack (compact, positional)
K={k:i for i,k in enumerate(KINDS)}; II={s:i for i,s in enumerate(INSTS)}; TFI={'5m':0,'15m':1,'1h':2,'session':3}
NAMES=[]; 
def ni(n):
    if n not in NAMES: NAMES.append(n)
    return NAMES.index(n)
LAB={'HH':0,'HL':1,'LH':2,'LL':3}; CLS={'manipulation':0,'delayed':1,'acceptance':2}; WINI={None:0,'London':1,'NY':2}
BTYP={'bos':0,'choch':1,'mss':2}; PK={'session':0,'swing':1,'eq':2}
EV_sorted=sorted(range(len(EV)),key=lambda k:EV[k]['t']); remap={old:new for new,old in enumerate(EV_sorted)}
TID={tr['id']:k for k,tr in enumerate(TRADES)}
def m(x): return x//60 if x else 0
packed=dict(t=[],i=[],f=[],k=[],p=[],x=[])
formed_key={}
prev=0
for new,old in enumerate(EV_sorted):
    e=EV[old]; tk=TICK[e['inst']]
    tt=e['t']//60; packed['t'].append(tt-prev); prev=tt
    packed['i'].append(II[e['inst']]); packed['f'].append(TFI[e['tf']]); packed['k'].append(K[e['kind']])
    P=lambda v: round(v/tk) if v is not None else None
    packed['p'].append(P(e['p']))
    k=e['kind']; x=0
    if k=='swing': x=LAB[e['lab']]
    elif k=='pool_formed': x=[ni(e['name']),1 if e['typ']=='H' else 0,PK[e['pk']],m(e['t_end']),1 if e['swept'] else 0,e['touches']]
    elif k=='sweep': x=[ni(e['name']),1 if e['typ']=='H' else 0,PK[e['pk']],CLS[e['cls']],WINI[e['win']],P(e['ext']),1 if e['smt'] else 0]
    elif k=='manip_leg': x=[P(e['q']),1 if e['typ']=='H' else 0]
    elif k=='smt': x=[ni(e['name']),1 if e['typ']=='H' else 0,II[e['pair']],round(e['pair_level']/TICK[e['pair']])]
    elif k=='structure_break': x=[BTYP[e['typ']],e['dir'],1 if e['disp'] else 0,m(e['t0'])]
    elif k=='mss_failed': x=[e['dir'],BTYP[e['typ']]]
    elif k=='inducement': x=[e['dir'],m(e['taken']),m(e['t_end'])]
    elif k in('fvg_formed','ob_formed'):
        x=[P(e['q']),e['dir'],m(e['t_end']),m(e['mit']),m(e['inv'])]; formed_key[(k[:3],e['inst'],e['tf'],e['t'],e['p'])]=new
    elif k in('fvg_inverted','ob_mitigated','ob_invalidated'):
        x=[P(e['q']),e['dir']]
    elif k=='session_open': x=ni(e['name'])
    elif k=='fire': x=[TID[e['trade']]]
    elif k=='ob_entry': x=[TID[e['trade']]]
    elif k=='refusal': x=[TID[e['trade']],e['step']]
    elif k=='outcome': x=[TID[e['trade']],e['R']]
    packed['x'].append(x)
def pack_bars(s,bars):
    tk=TICK[s]; t=[];o=[];h=[];l=[];c=[];v=[]
    prev_t=None; prev_c=None
    for b in bars:
        tt=b['t']//60; t.append(tt-(prev_t or 0)); prev_t=tt
        oo=round(b['o']/tk); hh=round(b['h']/tk); ll=round(b['l']/tk); cc=round(b['c']/tk)
        o.append(oo-(prev_c if prev_c is not None else 0)); h.append(hh-oo); l.append(oo-ll); c.append(cc-oo); prev_c=cc; v.append(int(b['v']))
    sdl=[str(b['sd']) for b in bars]; runs=[]
    for x in sdl:
        if runs and runs[-1][0]==x: runs[-1][1]+=1
        else: runs.append([x,1])
    return dict(tick=tk,t=t,o=o,h=h,l=l,c=c,v=v,sd=runs)
chart={s:{'5m':pack_bars(s,BARS[s]['5m'])} for s in ['NQ','ES','YM','RTY']}
for s in B2: chart[s]['2m']=pack_bars(s,B2[s])
TR=[]
for tr in TRADES:
    t=dict(tr)
    for k in ('sweep_t','mss_t','fill_t','exit_t'):
        if k in t and t[k]: t[k]=t[k]//60
    t.pop('sweep_ev',None)
    t['steps']={k:(v if isinstance(v,list) else [1 if v['ok'] else 0,v['why']]) for k,v in t['steps'].items()}
    for k in ('pool_p','entry','stop','target','exit'):
        if k in t and isinstance(t[k],float): t[k]=round(t[k],3)
    TR.append(t)
lv={s:{d:{n:round(v,3) for n,v in x.items()} for d,x in LEVELS[s].items()} for s in INSTS}
DESK=[]
_dp=os.path.join(ROOT,'data','desk_calls.jsonl')
if os.path.exists(_dp):
    feedmap={t['key']:t for t in TRADES if t.get('route')=='feed'}
    for line in open(_dp):
        try: k=json.loads(line)
        except Exception: continue
        o=feedmap.get(k['key']); k['R']=o['R'] if o else None; k['filled']=bool(o); DESK.append(k)
KRON=None
_kp=os.path.join(ROOT,'data','kronos.json')
if os.path.exists(_kp):
    try: KRON=json.load(open(_kp))
    except Exception: KRON=None
elif os.environ.get('KRONOS_URL'):
    try: KRON=json.loads(urllib.request.urlopen(os.environ['KRONOS_URL'],timeout=20).read())
    except Exception: KRON=None
_mp=os.path.join(ROOT,'data','mistakes.json'); MIST=json.load(open(_mp)) if os.path.exists(_mp) else None
_sp=os.path.join(ROOT,'data','scout.json'); SCOUT=json.load(open(_sp)) if os.path.exists(_sp) else None
out=dict(scout=SCOUT,mistakes=MIST,kronos=KRON,orb=ORB,desk=DESK,bt=BT,lab=LABOUT,sig=SIG,rules=RULES_VERSION,days=[str(d) for d in days],kinds=KINDS,insts=INSTS,names=NAMES,tick=TICK,events=packed,trades=TR,chart=chart,levels=lv,generated=dt.datetime.now(NY).strftime('%Y-%m-%d %H:%M'),two_min_from=str(B2['NQ'][0]['sd']))
json.dump(out,open(os.path.join(ROOT,'data','farm.json'),'w'),separators=(',',':'))
c=collections.Counter(e['kind'] for e in EV)
print(len(days),'days',len(EV),'events',c)
ch=[t for t in TRADES if t['route']=='chain']; f=[t for t in ch if t['fired']]
print('chain sweeps in window',len(ch),'fired',len(f),'grossR',round(sum(t['R'] for t in f),2),'wins',sum(t['R']>0 for t in f))
sh=[t for t in ch if not t['fired'] and 'R' in t]; print('shadow',len(sh),round(sum(t['R'] for t in sh),2))
ob=[t for t in TRADES if t['route']=='ob' and t['fired']]; print('ob',len(ob),round(sum(t['R'] for t in ob),2),sum(t['R']>0 for t in ob))
print(collections.Counter(t['failed'][0] if t['failed'] else 'fired' for t in ch))
print('farm written')
