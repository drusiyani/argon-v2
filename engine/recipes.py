"""Recipe engine: tests a new strategy idea, written as a small 'recipe', on years of real futures, honestly.

A recipe can only be built from a fixed menu of pieces the engine understands (below), so an AI can suggest ideas but
can't sneak in anything untestable. Every piece only uses information from before the entry minute. Trading costs are
always on. Each recipe may try at most 12 settings, re-picked monthly from the previous 6 months (the same honest
method as the rest of Argon), and it must beat entering at the same moment in a random direction.
"""
import os,json,gzip,csv,glob,math,random,itertools,collections,datetime as dt
from zoneinfo import ZoneInfo
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); NY=ZoneInfo('America/New_York')
COSTPTS={'NQ':0.75,'ES':0.5,'YM':3.0,'RTY':0.3}; LOOK=6; MAX_VARIANTS=12
MENU={'signal':{'range_breakout':['minutes'],'gap':['mode','min_gap_atr'],'prior_day_break':['mode'],'time_momentum':['at','mode'],'stretch_fade':['sigma']},
      'filters':['trend20','skip_monday','skip_friday','calm_days','busy_days'],'stop':{'atr':['frac'],'range':[]},'exit':{'R':['mult'],'close':[]}}
_DAYS={}
def load(sym):
    """1-minute regular-session candles (09:30-16:00 New York) per day, from the Databento files."""
    if sym in _DAYS: return _DAYS[sym]
    days=collections.defaultdict(list); off={}
    for f in sorted(glob.glob(os.path.join(ROOT,'data','databento',f'{sym}_*.csv.gz'))):
        with gzip.open(f,'rt') as fh:
            r=csv.reader(fh); next(r)
            for row in r:
                ts=row[0]; d0=ts[:10]
                if d0 not in off:
                    t=dt.datetime(int(ts[:4]),int(ts[5:7]),int(ts[8:10]),12,tzinfo=dt.timezone.utc); off[d0]=t.astimezone(NY).utcoffset().total_seconds()/60
                m=(int(ts[11:13])*60+int(ts[14:16])+off[d0])
                day=d0
                if m<0: m+=1440; day=(dt.date.fromisoformat(d0)-dt.timedelta(days=1)).isoformat()
                elif m>=1440: m-=1440; day=(dt.date.fromisoformat(d0)+dt.timedelta(days=1)).isoformat()
                if 570<=m<960: days[day].append((int(m),float(row[4]),float(row[5]),float(row[6]),float(row[7])))
    out={}
    for d,rows in days.items():
        rows.sort()
        if len(rows)>=300 and rows[0][0]==570: out[d]=rows
    _DAYS[sym]=dict(sorted(out.items())); return _DAYS[sym]
def walk(rows,i0,side,entry,stop,target,cost,risk):
    for m,o,h,l,c in rows[i0:]:
        if m>=959: return (c-entry)*side/risk-cost/risk
        if (l<=stop) if side==1 else (h>=stop): return (stop-entry)*side/risk-cost/risk
        if target is not None and ((h>=target) if side==1 else (l<=target)): return (target-entry)*side/risk-cost/risk
    return (rows[-1][4]-entry)*side/risk-cost/risk
def hm(s): h,m=s.split(':'); return int(h)*60+int(m)
def signals(rows,ctx,sig,p,rng=None):
    """Returns (entry_index, side, entry_price, range_hi, range_lo) or None, using only candles before entry_index."""
    t=sig['type']; op=rows[0][1]
    if t=='range_breakout':
        n=p['minutes']; first=[x for x in rows if x[0]<570+n]; hi=max(x[2] for x in first); lo=min(x[3] for x in first)
        for i in range(len(first),len(rows)):
            if rows[i][0]>=900: return None
            if rows[i-1][4]>hi: return (i,1,rows[i][1],hi,lo)
            if rows[i-1][4]<lo: return (i,-1,rows[i][1],hi,lo)
        return None
    if t=='gap':
        g=op-ctx['prev_close']
        if not ctx['atr'] or abs(g)<p['min_gap_atr']*ctx['atr']: return None
        side=(-1 if g>0 else 1) if p['mode']=='fade' else (1 if g>0 else -1)
        return (1,side,rows[1][1],None,None)
    if t=='prior_day_break':
        for i in range(1,len(rows)):
            if rows[i][0]>=900: return None
            c=rows[i-1][4]
            if c>ctx['pdh'] or c<ctx['pdl']:
                up=c>ctx['pdh']; side=(1 if up else -1) if p['mode']=='follow' else (-1 if up else 1)
                return (i,side,rows[i][1],None,None)
        return None
    if t=='time_momentum':
        T=hm(p['at']); i=next((k for k,x in enumerate(rows) if x[0]>=T),None)
        if i is None or i==0: return None
        mv=rows[i-1][4]-op
        if mv==0: return None
        side=(1 if mv>0 else -1) if p['mode']=='follow' else (-1 if mv>0 else 1)
        return (i,side,rows[i][1],None,None)
    if t=='stretch_fade':
        if not ctx['mv14']: return None
        for i in range(1,len(rows)):
            if rows[i][0]>=900: return None
            mv=rows[i-1][4]-op
            if abs(mv)>p['sigma']*ctx['mv14']: return (i,-1 if mv>0 else 1,rows[i][1],None,None)
        return None
    raise ValueError(t)
def grid(recipe):
    parts=[]
    for sect in ('signal','stop','exit'):
        for k,v in recipe[sect].items():
            if k!='type': parts.append((sect,k,v if isinstance(v,list) else [v]))
    combos=list(itertools.product(*[x[2] for x in parts])) or [()]
    out=[]
    for c in combos:
        p={'signal':{},'stop':{},'exit':{}}
        for (sect,k,_),val in zip(parts,c): p[sect][k]=val
        out.append(p)
    return out
def critic_static(recipe):
    """The automatic critic: checks the recipe before anything is tested."""
    probs=[]
    sig=recipe.get('signal',{}); st=recipe.get('stop',{}); ex=recipe.get('exit',{})
    if sig.get('type') not in MENU['signal']: probs.append(f"unknown signal '{sig.get('type')}'")
    else:
        for k in MENU['signal'][sig['type']]:
            if k not in sig: probs.append(f"signal is missing '{k}'")
    if st.get('type') not in MENU['stop']: probs.append(f"unknown stop '{st.get('type')}'")
    if st.get('type')=='range' and sig.get('type')!='range_breakout': probs.append("a range stop only works with a range breakout")
    if ex.get('type') not in MENU['exit']: probs.append(f"unknown exit '{ex.get('type')}'")
    for f in recipe.get('filters',[]):
        if f not in MENU['filters']: probs.append(f"unknown filter '{f}'")
    for m in recipe.get('markets',[]):
        if m not in COSTPTS: probs.append(f"unknown market '{m}'")
    if not probs:
        n=len(grid(recipe))
        if n>MAX_VARIANTS: probs.append(f"tries {n} settings; the limit is {MAX_VARIANTS} (more tries = more chance of a lucky fluke)")
    return probs
def daily_ctx(days,keys,i):
    prev=days[keys[i-1]] if i else None
    if not prev: return None
    rngs=[max(x[2] for x in days[k])-min(x[3] for x in days[k]) for k in keys[max(0,i-14):i]]
    mvs=[]
    for k in keys[max(0,i-14):i]:
        r=days[k]; o=r[0][1]; mvs.append(sum(abs(x[4]-o) for x in r)/len(r))
    closes=[days[k][-1][4] for k in keys[max(0,i-20):i]]
    return dict(prev_close=prev[-1][4],pdh=max(x[2] for x in prev),pdl=min(x[3] for x in prev),atr=sum(rngs)/len(rngs) if rngs else None,
                mv14=sum(mvs)/len(mvs) if mvs else None,trend_up=(prev[-1][4]>sum(closes)/len(closes)) if len(closes)>=20 else None,
                range_today_atr=None)
def run_recipe(recipe,random_dir=False,seed=0):
    """Every trade for every setting: {setting_index: [(month, R)]}."""
    rng=random.Random(seed); G=grid(recipe); res=collections.defaultdict(list); flt=set(recipe.get('filters',[]))
    for sym in recipe['markets']:
        days=load(sym); keys=list(days); cost=COSTPTS[sym]
        for i,k in enumerate(keys):
            ctx=daily_ctx(days,keys,i)
            if not ctx or not ctx['atr']: continue
            wd=dt.date.fromisoformat(k).weekday()
            if ('skip_monday' in flt and wd==0) or ('skip_friday' in flt and wd==4): continue
            rows=days[k]; month=k[:7]
            for gi,p in enumerate(G):
                s=signals(rows,ctx,recipe['signal'],p['signal'])
                if not s: continue
                i0,side,entry,hi,lo=s
                if random_dir: side=rng.choice((1,-1))
                if 'trend20' in flt and (ctx['trend_up'] is None or (side==1)!=ctx['trend_up']): continue
                if 'calm_days' in flt or 'busy_days' in flt:
                    sofar=max(x[2] for x in rows[:i0])-min(x[3] for x in rows[:i0])
                    if 'calm_days' in flt and sofar>0.5*ctx['atr']: continue
                    if 'busy_days' in flt and sofar<0.5*ctx['atr']: continue
                st=recipe['stop']
                if st['type']=='range': stop=lo if side==1 else hi
                else: stop=entry-side*p['stop']['frac']*ctx['atr']
                risk=(entry-stop)*side
                if risk<=0: continue
                ex=recipe['exit']; target=entry+side*p['exit']['mult']*risk if ex['type']=='R' else None
                res[gi].append((month,walk(rows,i0,side,entry,stop,target,cost,risk)))
    return G,res
def sharpe(monthly):
    """Annualised Sharpe ratio from monthly results: average month / how much months vary x sqrt(12)."""
    if len(monthly)<3: return 0.0
    mu=sum(monthly)/len(monthly); sd=(sum((x-mu)**2 for x in monthly)/(len(monthly)-1))**.5
    return round(mu/sd*math.sqrt(12),2) if sd>0 else 0.0
def walk_forward(G,res,months):
    """Each month, use the setting that did best over the previous 6 months. Returns the honest monthly results."""
    mon={gi:collections.defaultdict(float) for gi in range(len(G))}; cnt={gi:collections.Counter() for gi in range(len(G))}
    for gi,rows in res.items():
        for m,r in rows: mon[gi][m]+=r; cnt[gi][m]+=1
    out=[]
    for i,m in enumerate(months):
        if i<LOOK: continue
        prev=months[i-LOOK:i]; best=max(range(len(G)),key=lambda g:sum(mon[g][x] for x in prev))
        out.append(dict(month=m,R=round(mon[best][m],2),n=cnt[best][m],pick=best))
    return out
def summarise(series):
    eq=pk=dd=0; R=[x['R'] for x in series]
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    half=len(series)//2
    return dict(months=len(series),n=sum(x['n'] for x in series),R=round(sum(R),1),dd=round(dd,1),up=sum(1 for x in R if x>0),sharpe=sharpe(R),
                first_half=round(sum(R[:half]),1),second_half=round(sum(R[half:]),1))
def test(recipe,n_random=10):
    probs=critic_static(recipe)
    if probs: return dict(verdict='rejected before testing',problems=probs)
    G,res=run_recipe(recipe); months=sorted({m for rows in res.values() for m,_ in rows})
    wf=walk_forward(G,res,months); S=summarise(wf)
    rnd=[]
    for s in range(n_random):
        Gr,rr=run_recipe(recipe,random_dir=True,seed=s); rnd.append(summarise(walk_forward(Gr,rr,months))['sharpe'])
    rnd.sort(); beat=sum(1 for x in rnd if S['sharpe']>x)
    checks=[('at least 150 trades',S['n']>=150),('made money after costs',S['R']>0),('made money in both halves',S['first_half']>0 and S['second_half']>0),
            (f'Sharpe beats random entries ({beat}/{len(rnd)})',beat>=int(0.9*len(rnd))),('Sharpe of at least 0.5',S['sharpe']>=0.5)]
    passed=sum(ok for _,ok in checks)
    verdict='promising: worth a forward test' if passed==len(checks) else 'not good enough' if passed<=3 else 'close, but not convincing'
    return dict(verdict=verdict,checks=[[c,bool(ok)] for c,ok in checks],summary=S,random_sharpe=dict(median=rnd[len(rnd)//2],best=rnd[-1]),variants=len(G),
                curve=[[x['month'],x['R']] for x in wf])
if __name__=='__main__':
    import sys,time
    SEED=[dict(name='Gap fade',idea='Big overnight gaps tend to partly close in the first hours.',source='seed example',markets=['NQ','ES','YM','RTY'],
               signal=dict(type='gap',mode='fade',min_gap_atr=[0.15,0.3]),filters=[],stop=dict(type='atr',frac=[0.15,0.3]),exit=dict(type='R',mult=[1,2])),
          dict(name='Ten-o-clock momentum',idea='The first 30 minutes set the tone: follow the move from the open at 10:00.',source='seed example',markets=['NQ','ES','YM','RTY'],
               signal=dict(type='time_momentum',at=['10:00','10:30'],mode='follow'),filters=['trend20'],stop=dict(type='atr',frac=[0.15,0.3]),exit=dict(type='close')),
          dict(name='Too many settings',idea='A deliberately over-tuned recipe, to check the critic stops it.',source='seed example',markets=['NQ'],
               signal=dict(type='range_breakout',minutes=[5,10,15,30]),filters=[],stop=dict(type='atr',frac=[0.1,0.2,0.3]),exit=dict(type='R',mult=[1,2,3]))]
    for r in SEED:
        t=time.time(); out=test(r); out.pop('curve',None); print(r['name'],round(time.time()-t),'s',json.dumps(out)[:600])
