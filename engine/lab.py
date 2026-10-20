import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import time; T0=time.time()
exec(open(os.path.join(ROOT,'engine','backtest_core.py')).read())
import itertools, json, random
# daily bias: previous session up or down
DAILY={}
for s in TRADED:
    bars=BARS[s]['5m']
    for di,sd in enumerate(days):
        if di==0: continue
        pi=SESS_IDX[s][days[di-1]]
        if pi: DAILY[(s,sd)]=1 if bars[pi[-1]]['c']>bars[pi[0]]['o'] else -1
for c in CANDS:
    c['daily']=DAILY.get((c['s'],c['sw']['sd']),0)==c['d']
    c['nyopen']=c['sw']['win']=='NY' and 870<=smin(c['sw']['t'] and BARS[c['s']]['5m'][c['sw']['i']]['m'])<960
    c['month']=c['sd'][:7]
for c in OBC: c['month']=c['sd'][:7]
# new ideas: first trap of the session, skip the 8:30 news spike, skip tiny stops
_first={}
for c in sorted(CANDS,key=lambda c:c['sw']['t']):
    k=(c['s'],c['sd'],c['sw']['win']); c['first']=k not in _first; _first[k]=1
    mm=BARS[c['s']]['5m'][c['sw']['i']]['m']; c['news']=505<=mm<525
    c['atr']=ATR[c['s']]['5m'][c['sw']['i']]
RISK=dict(min_rr=1.5,max_entries=5,day_loss=-2.0)
MK={'all':tuple(TRADED),'nq':('NQ',),'es':('ES',)}
WN={'ny':'NY','london':'London'}
def pick_sim(c,r):
    for kd in {'fvg_first':('fvg','ob'),'ob_first':('ob','fvg')}[r['entry']]:
        sm=c['sims'].get((kd,r['target']))
        if sm is not None: return sm
    return None
CS=sorted(CANDS,key=lambda c:c['sw']['t'])
def run(r):
    out=[]; busy={}; day_n=collections.Counter(); day_loss=collections.defaultdict(float)
    mk=MK[r['markets']]
    for c in CS:
        if c['s'] not in mk: continue
        w=r['windows']
        if w=='ny_open':
            if not c['nyopen']: continue
        elif w!='both' and c['sw']['win']!=WN[w]: continue
        pl=r['pool']; pk=c['p']['kind']; ptf=c['p']['tf']
        if pl=='quality' and not c['st']['1'][0]: continue
        if pl=='session' and pk!='session': continue
        if pl=='eq' and pk!='eq': continue
        if pl=='htf' and not (pk=='session' or ptf in ('15m','1h')): continue
        if r.get('sweep')=='instant' and c['sw']['cls']!='manipulation': continue
        if r.get('first')=='yes' and not c['first']: continue
        if r.get('news')=='skip' and c['news']: continue
        if not c['st']['2'][0] or not c['st']['4'][0]: continue
        if r['smt']=='required' and not c['st']['3'][0]: continue
        sm=pick_sim(c,r)
        if not sm or sm['fill'] is None: continue
        if r.get('minstop')=='half_atr' and sm['risk']<0.5*c['atr']: continue
        b=r['bias']
        if b=='h1' and not c['h1']: continue
        if b=='daily' and not c['daily']: continue
        if b=='pd':
            if not c['eqm'] or not ((sm['entry']>c['eqm']) if c['d']==-1 else (sm['entry']<c['eqm'])): continue
        if r.get('risk',True):
            if sm['rr']<RISK['min_rr'] or day_n[c['sd']]>=RISK['max_entries'] or day_loss[c['sd']]<=RISK['day_loss']: continue
        if sm['fill']<=busy.get(c['s'],-1): continue
        be=r.get('manage')=='be1'; Rr=sm['R_be'] if be else sm['R']
        busy[c['s']]=sm['exit_k_be'] if be else sm['exit_k']; day_n[c['sd']]+=1; day_loss[c['sd']]+=Rr
        out.append((c['month'],Rr,c['sd'],c))
    return out
def run_ob(r):
    out=[]; busy={}; mk=MK[r['markets']]
    for c in sorted(OBC,key=lambda c:c['t']):
        if c['s'] not in mk or c['win'] is None: continue
        w=r['windows']
        if w=='ny_open':
            if not (c['win']=='NY' and c['hour']<10): continue
        elif w!='both' and c['win']!=WN[w]: continue
        if not c['h1'] or c['rr']<RISK['min_rr'] or c['k0']<=busy.get(c['s'],-1): continue
        w=c['w']['be'] if r.get('manage')=='be1' else c['w']
        busy[c['s']]=w['k']; out.append((c['month'],w['R'],c['sd'],c))
    return out
MONTHS=sorted(set(c['month'] for c in CANDS))
DIALS=dict(entry=['fvg_first','ob_first'],windows=['both','ny','london','ny_open'],bias=['none','h1','pd','daily'],smt=['required','optional'],pool=['quality','session','eq','htf'],markets=['all','nq','es'],target=['pool','2R'],manage=['none'],sweep=['any','instant'],first=['no','yes'],news=['keep','skip'],minstop=['any','half_atr'])
if os.environ.get('LAB_WINDOWS'): DIALS['windows']=os.environ['LAB_WINDOWS'].split(',')   # e.g. london only
VARS=[]
for combo in itertools.product(*DIALS.values()):
    r=dict(zip(DIALS.keys(),combo)); tr=run(r)
    mon=collections.defaultdict(lambda:[0,0.0,0]); 
    for m,Rr,sd,c in tr: x=mon[m]; x[0]+=1; x[1]+=Rr; x[2]+=1 if Rr>0 else 0
    VARS.append(dict(route='chain',rules=r,mon={m:tuple(v) for m,v in mon.items()},trades=tr))
for combo in itertools.product(['all','nq','es'],['both','ny','london','ny_open'],['none','be1']):
    r=dict(markets=combo[0],windows=combo[1],manage=combo[2]); tr=run_ob(r)
    mon=collections.defaultdict(lambda:[0,0.0,0])
    for m,Rr,sd,c in tr: x=mon[m]; x[0]+=1; x[1]+=Rr; x[2]+=1 if Rr>0 else 0
    VARS.append(dict(route='ob',rules=r,mon={m:tuple(v) for m,v in mon.items()},trades=tr))
print('variants',len(VARS),round(time.time()-T0))
BASE=dict(entry='fvg_first',windows='both',bias='none',smt='required',pool='quality',markets='all',target='pool',manage='none',sweep='any',first='no',news='keep',minstop='any')
OBBASE=dict(markets='all',windows='both',manage='none')
if os.environ.get('LAB_WINDOWS'): BASE['windows']=DIALS['windows'][0]   # the comparison uses the same sessions
def find(route,r): return next(V for V in VARS if V['route']==route and V['rules']==r)
LOOK=6; MIN_N=30
def agg(V,ms):
    n=sum(V['mon'].get(m,(0,0,0))[0] for m in ms); R_=sum(V['mon'].get(m,(0,0,0))[1] for m in ms); return n,R_
def adaptive(route,base):
    cur=find(route,base); log=[]
    for k,m in enumerate(MONTHS):
        if k>=LOOK:
            prev=MONTHS[k-LOOK:k]; h1,h2=prev[:LOOK//2],prev[LOOK//2:]
            best=None
            for V in VARS:
                if V['route']!=route: continue
                n,R_=agg(V,prev)
                if n<MIN_N or R_<=0: continue
                if agg(V,h1)[1]<=0 or agg(V,h2)[1]<=0: continue
                score=R_/n
                if best is None or score>best[0]: best=(score,V)
            changed=False
            if best and best[1] is not cur: cur=best[1]; changed=True
            pick_ok=best is not None
        else: changed=False; pick_ok=None
        n,R_,w=cur['mon'].get(m,(0,0.0,0))
        log.append(dict(month=m,rules=cur['rules'],n=n,R=round(R_,2),w=w,changed=changed,qualified=pick_ok))
    return log
AD=adaptive('chain',BASE); ADOB=adaptive('ob',OBBASE)
OOS=MONTHS[LOOK:]
def series(V): return [round(V['mon'].get(m,(0,0,0))[1],2) for m in MONTHS]
baseV=find('chain',BASE); obV=find('ob',OBBASE)
hind=max([V for V in VARS if V['route']=='chain'],key=lambda V:agg(V,MONTHS)[1])
def summ(rows):
    n=sum(r['n'] for r in rows); R_=sum(r['R'] for r in rows); w=sum(r['w'] for r in rows); eq=pk=dd=0
    for r in rows: eq+=r['R']; pk=max(pk,eq); dd=min(dd,eq-pk)
    mr=[r['R'] for r in rows]; mu=sum(mr)/len(mr) if mr else 0; sd=(sum((x-mu)**2 for x in mr)/(len(mr)-1))**.5 if len(mr)>2 else 0
    sh=round(mu/sd*12**.5,2) if sd>0 else 0.0      # Sharpe ratio: average month / how much months vary, per year
    return dict(n=n,R=round(R_,2),wr=round(w/n,3) if n else 0,dd=round(dd,2),months_up=sum(1 for r in rows if r['R']>0),months=len(rows),sharpe=sh)
def summV(V,ms): return summ([dict(n=V['mon'].get(m,(0,0,0))[0],R=V['mon'].get(m,(0,0,0))[1],w=V['mon'].get(m,(0,0,0))[2]) for m in ms])
adO=[r for r in AD if r['month'] in OOS]; adobO=[r for r in ADOB if r['month'] in OOS]
print('adaptive chain OOS',summ(adO)); print('baseline chain OOS',summV(baseV,OOS)); print('hindsight',hind['rules'],summV(hind,MONTHS))
print('adaptive ob OOS',summ(adobO)); print('ob base OOS',summV(obV,OOS))
print('changes',sum(r['changed'] for r in AD),'months sitting on baseline',sum(1 for r in adO if r['qualified'] is False))
# current pick for v0.4: what the process would trade in October 2026
def pick_now(route,base):
    prev=MONTHS[-LOOK:]; h1,h2=prev[:LOOK//2],prev[LOOK//2:]; best=None
    for V in VARS:
        if V['route']!=route: continue
        n,R_=agg(V,prev)
        if n<MIN_N or R_<=0 or agg(V,h1)[1]<=0 or agg(V,h2)[1]<=0: continue
        if best is None or R_/n>best[0]: best=(R_/n,V)
    return best[1] if best else None
NOWC=pick_now('chain',BASE); NOWOB=pick_now('ob',OBBASE)
print('now chain',NOWC and NOWC['rules'], NOWC and summV(NOWC,MONTHS[-LOOK:]))
print('now ob',NOWOB and NOWOB['rules'], NOWOB and summV(NOWOB,MONTHS[-LOOK:]))
# importance across all 33 months
IMP={}
for dk,vals in DIALS.items():
    IMP[dk]={}
    for v in vals:
        xs=[agg(V,MONTHS) for V in VARS if V['route']=='chain' and V['rules'][dk]==v]
        xs=[R_/n for n,R_ in xs if n>=50]
        IMP[dk][v]=[round(sum(xs)/len(xs),3),len(xs)] if xs else [None,0]
# breakdowns for baseline across full period
def brk(V,fn):
    d=collections.defaultdict(lambda:[0,0.0,0])
    for m,Rr,sd,c in V['trades']:
        k=fn(c); x=d[k]; x[0]+=1; x[1]+=Rr; x[2]+=Rr>0
    return {k:[v[0],round(v[1],2),round(v[2]/v[0],3)] for k,v in d.items()}
allchain=[V for V in VARS if V['route']=='chain']
yrs=sorted(set(m[:4] for m in MONTHS))
import random as _rnd
_pool=[V for V in VARS if V['route']=='chain' and agg(V,OOS)[0]>=MIN_N]; _rnd.Random(1).shuffle(_pool)
def _cum(V):
    t=0; out=[]
    for m in OOS: t+=V['mon'].get(m,(0,0,0))[1]; out.append(round(t,1))
    return out
FAN=dict(months=OOS,curves=[_cum(V) for V in _pool[:150]],n_total=len(_pool))
def _msr(V):   # monthly Sharpe of one version over the unseen months (for the deflated Sharpe ratio)
    xs=[V['mon'].get(m,(0,0,0))[1] for m in OOS]; mu=sum(xs)/len(xs); sd=(sum((x-mu)**2 for x in xs)/(len(xs)-1))**.5
    return mu/sd if sd>0 else 0.0
_srs=[_msr(V) for V in _pool]; _mu=sum(_srs)/len(_srs) if _srs else 0
TRIALS=dict(n_lab=len(_srs),sr_mean=round(_mu,4),sr_var=round(sum((x-_mu)**2 for x in _srs)/max(1,len(_srs)-1),6),
            n_project=33000,note='n_project: every version tried across all of Argon v2 rounds (logged in the Lab history), the honest count for the deflated Sharpe')   # every faint line on the site's fan chart is one version
OUT=dict(trials=TRIALS,fan=FAN,range=[str(days[0]),str(days[-1])],sessions=len(days),months=MONTHS,look=LOOK,min_n=MIN_N,n_variants=len(VARS),n_cands=len(CANDS),n_obc=len(OBC),
 adaptive=AD,adaptive_ob=ADOB,base=series(baseV),base_ob=series(obV),hind=series(hind),hind_rules=hind['rules'],
 sum=dict(adaptive=summ(adO),base=summV(baseV,OOS),hind=summV(hind,OOS),adaptive_ob=summ(adobO),base_ob=summV(obV,OOS)),
 by_year={y:dict(adaptive=summ([r for r in adO if r['month'][:4]==y]),base=summV(baseV,[m for m in OOS if m[:4]==y])) for y in yrs},
 now=dict(chain=NOWC and dict(rules=NOWC['rules'],last6=summV(NOWC,MONTHS[-LOOK:]),all=summV(NOWC,MONTHS)),ob=NOWOB and dict(rules=NOWOB['rules'],last6=summV(NOWOB,MONTHS[-LOOK:]),all=summV(NOWOB,MONTHS))),
 importance=IMP,dials=DIALS,
 base_by_market=brk(baseV,lambda c:c['s']),base_by_session=brk(baseV,lambda c:c['sw']['win']),base_by_side=brk(baseV,lambda c:c['side']),
 source=('Databento: real CME futures 1-minute candles (NQ, ES, YM, RTY), front month rolled by volume' if SOURCE=='databento' else 'HistData.com 1-minute CFD prices (Nasdaq, S&P 500)')+', turned into 5-minute candles')
try:
    PREV=json.load(open((os.environ.get('LAB_OUT') or os.path.join(ROOT,'data','bt_out.json'))))
    OUT['prev_now']=PREV.get('now'); OUT['prev_sum']=PREV.get('sum')
except Exception: pass
json.dump(OUT,open((os.environ.get('LAB_OUT') or os.path.join(ROOT,'data','bt_out.json')),'w'))
print('done',round(time.time()-T0))
# ---- meta test: how far back to look, and whether to stick with the current rules unless clearly beaten
def adaptive2(route,base,look,hyst):
    cur=find(route,base); log=[]
    for k,m in enumerate(MONTHS):
        if k>=look:
            prev=MONTHS[k-look:k]; h1,h2=prev[:look//2],prev[look//2:]
            def sc(V):
                n,R_=agg(V,prev)
                if n<max(15,MIN_N*look//6) or R_<=0 or agg(V,h1)[1]<=0 or agg(V,h2)[1]<=0: return None
                return R_/n
            best=None
            for V in VARS:
                if V['route']!=route: continue
                x=sc(V)
                if x is not None and (best is None or x>best[0]): best=(x,V)
            cs=sc(cur)
            if best and best[1] is not cur and (cs is None or best[0]>cs+hyst): cur=best[1]
        n,R_,w=cur['mon'].get(m,(0,0.0,0)); log.append(dict(month=m,rules=cur['rules'],n=n,R=round(R_,2),w=w))
    return log
COMMON=MONTHS[12:]
META=[]
for look in (6,):
    for hy in (0.0,0.15):
        for route,base in (('chain',BASE),('ob',OBBASE)):
            lg=adaptive2(route,base,look,hy); rows=[r for r in lg if r['month'] in COMMON]
            ch=sum(1 for a,b in zip(lg,lg[1:]) if a['rules']!=b['rules'] and b['month'] in COMMON)
            META.append(dict(route=route,look=look,hyst=hy,changes=ch,**summ(rows)))
for x in META: print(x)
OUT['meta']=META; OUT['common_from']=COMMON[0]
json.dump(OUT,open((os.environ.get('LAB_OUT') or os.path.join(ROOT,'data','bt_out.json')),'w'))
# ---- raw findings for the brain (vault): every window sweep and every day, compact
rows=[]
for c in CS:
    sw=c['sw']; p=c['p']; sm=c['sims'].get(('ob','2R')) or c['sims'].get(('fvg','2R'))
    rows.append([c['s'],c['sd'],c['hour'],sw['win'],p['name'],p['kind'],p['tf'],c['side'],sw['cls'],1 if sw['smt'] else 0,1 if c['h1'] else 0,1 if c['daily'] else 0,1 if c['m'] else 0,1 if (c['m'] and c['m']['disp']) else 0,None if not sm or sm['fill'] is None else sm['R'],c['dow']])
json.dump(dict(cols=['inst','day','hour','session','level','level_kind','level_tf','side','sweep','smt','h1','daily','flip','flip_big','R_2R','dow'],rows=rows),open(os.path.join(ROOT,'data','bt_cands.json'),'w'))
drows=[]
for s in TRADED:
    bars=BARS[s]['5m']
    for sd in days:
        idx=SESS_IDX[s][sd]
        if not idx: continue
        b=[bars[i] for i in idx]
        def rng(a,z):
            x=[q for q in b if a<=smin(q['m'])<z]
            return round(max(q['h'] for q in x)-min(q['l'] for q in x),2) if x else None
        drows.append([s,str(sd),b[0]['dow'],round(max(q['h'] for q in b)-min(q['l'] for q in b),2),rng(120,360),rng(480,660),rng(870,1050),round(b[-1]['c']-b[0]['o'],2),round(b[0]['o'],2)])
json.dump(dict(cols=['inst','day','dow','range','asia','london','ny','change','open'],rows=drows),open(os.path.join(ROOT,'data','bt_days.json'),'w'))
print('brain dumps',len(rows),len(drows))
