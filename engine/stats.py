"""How sure are we? Confidence ranges, the deflated Sharpe ratio, benchmarks and realistic sizing, on the unseen months.
  - block bootstrap: resample the monthly results in 3-month blocks (keeps bad runs together), 5,000 times
  - day-clustered bootstrap: every trade from the same day is resampled together, across markets (they are one bet)
  - deflated Sharpe (Bailey & Lopez de Prado, 2014): discounts the Sharpe for how many versions were tried
  - benchmarks: buy-and-hold Nasdaq and S&P futures, and entering at the same moments in a random direction
  - micro contracts: whole MNQ contracts only, with micro-sized costs
Writes data/stats.json."""
import os,json,math,random,collections,statistics as st
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bt=json.load(open(os.path.join(ROOT,'data','bt_out.json'))); orb=json.load(open(os.path.join(ROOT,'data','orb_out.json')))
OOS=bt['months'][bt['look']:]; main={r['month']:r['R'] for r in bt['adaptive']}
nq={x[0]:x[1] for x in orb['markets']['NQ']['series']}
SER={'Portfolio':[main.get(m,0)+nq.get(m,0) for m in OOS],'Main strategy':[main.get(m,0) for m in OOS],'Opening range Nasdaq':[nq.get(m,0) for m in OOS]}
def ncdf(x): return 0.5*(1+math.erf(x/2**.5))
def ninv(p):   # inverse normal (Acklam's approximation, plenty for this)
    a=[-3.969683028665376e+01,2.209460984245205e+02,-2.759285104469687e+02,1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00]
    b=[-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,6.680131188771972e+01,-1.328068155288572e+01]
    c=[-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,-2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00]
    d=[7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,3.754408661907416e+00]
    if p<0.02425: q=math.sqrt(-2*math.log(p)); return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p>1-0.02425: return -ninv(1-p)
    q=p-0.5; r=q*q; return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
def sharpe(x): mu=st.mean(x); sd=st.stdev(x); return mu/sd*12**.5 if sd>0 else 0.0
def sortino(x):
    mu=st.mean(x); dn=[min(0,v) for v in x]; dd=(sum(v*v for v in dn)/len(dn))**.5
    return mu/dd*12**.5 if dd>0 else 0.0
RISK=0.75   # % of the account per 1R (was 0.5 until 27 Oct 2026); site/src/app1.js has the same constant
def grow(x,risk):   # compounded, risk % of the account per 1R
    eq=1;pk=1;dd=0
    for v in x: eq*=max(0.0,1+v*risk/100); pk=max(pk,eq); dd=min(dd,eq/pk-1)
    return eq,dd
def cagr(x,risk=RISK): eq,_=grow(x,risk); return (eq**(12/len(x))-1)*100 if eq>0 else -100.0
def block_boot(x,n=5000,block=3,seed=7):
    rg=random.Random(seed); out=[]
    for _ in range(n):
        y=[]
        while len(y)<len(x): i=rg.randrange(0,len(x)-block+1); y+=x[i:i+block]
        out.append(y[:len(x)])
    return out
def pct(a,q): a=sorted(a); return a[min(len(a)-1,max(0,int(q*len(a))))]
def summary(x):
    B=block_boot(x); shs=[sharpe(y) for y in B]; cg=[cagr(y) for y in B]; dds=[grow(y,RISK)[1]*100 for y in B]
    return dict(sharpe=round(sharpe(x),2),sortino=round(sortino(x),2),cagr=round(cagr(x),1),max_dd=round(grow(x,RISK)[1]*100,1),
                sharpe_ci=[round(pct(shs,.025),2),round(pct(shs,.975),2)],cagr_ci=[round(pct(cg,.025),1),round(pct(cg,.975),1)],
                dd_median=round(pct(dds,.5),1),dd_bad=round(pct(dds,.05),1),p_losing=round(sum(1 for s in shs if s<=0)/len(shs),3))
def deflated(x,n_trials,sr_var):
    """Probability the true Sharpe is above zero after allowing for n_trials tries (monthly units)."""
    T=len(x); mu=st.mean(x); sd=st.stdev(x); sr=mu/sd
    sk=sum(((v-mu)/sd)**3 for v in x)/T; ku=sum(((v-mu)/sd)**4 for v in x)/T
    g=0.5772156649; sr0=math.sqrt(sr_var)*((1-g)*ninv(1-1/n_trials)+g*ninv(1-1/(n_trials*math.e)))
    z=(sr-sr0)*math.sqrt(T-1)/math.sqrt(max(1e-9,1-sk*sr+(ku-1)/4*sr*sr))
    return dict(dsr=round(ncdf(z),3),sr0_annual=round(sr0*12**.5,2),trials=n_trials)
OUT={'months':[OOS[0],OOS[-1],len(OOS)],'strategies':{}}
TR=bt.get('trials') or {}
for k,x in SER.items():
    s=summary(x)
    if TR: s['deflated_lab']=deflated(x,max(2,TR['n_lab']),TR['sr_var']); s['deflated_project']=deflated(x,TR['n_project'],TR['sr_var'])
    OUT['strategies'][k]=s
# day-clustered bootstrap of the opening range's average trade (all trades on the same day move together)
T=orb['markets']['NQ'].get('trades') or []
if T:
    byday=collections.defaultdict(list)
    for d,r,_ in T: byday[d].append(r)
    days=list(byday); rg=random.Random(11); means=[]
    for _ in range(5000):
        smp=[r for _ in days for r in byday[days[rg.randrange(len(days))]]]; means.append(st.mean(smp))
    OUT['orb_trade_mean']=dict(mean=round(st.mean([r for _,r,_ in T]),3),ci=[round(pct(means,.025),3),round(pct(means,.975),3)],days=len(days),trades=len(T))
    # whole micro contracts: MNQ is $2 a point; costs per micro: 2 ticks of slippage (0.5 pt) + $1.24 commission (0.62 pt)
    mm=collections.defaultdict(float); skipped=0
    for d,r,risk in T:
        n=int(1000*RISK//(risk*2))
        if n<1: skipped+=1; continue
        gross=r*risk+0.75; mm[d[:7]]+=n*2*(gross-1.12)/(1000*RISK)
    xs=[mm.get(m,0) for m in OOS]
    OUT['orb_micro']=dict(R=round(sum(xs),1),sharpe=round(sharpe(xs),2),skipped=skipped,note='$100,000 account, '+str(RISK)+'% risk, rounded down to whole MNQ contracts')
# benchmarks: buy and hold, and random entries
bh={}
for s,cl in (orb.get('bh') or {}).items():
    ms=[m for m in OOS if m in cl]; prev=None; rets=[]
    for m in sorted(cl):
        if prev is not None and m in OOS: rets.append((cl[m]/cl[prev]-1)*100)
        prev=m
    if rets:
        eq=1;pk=1;dd=0
        for v in rets: eq*=1+v/100; pk=max(pk,eq); dd=min(dd,eq/pk-1)
        mu=st.mean(rets); sd=st.stdev(rets)
        bh[s]=dict(sharpe=round(mu/sd*12**.5,2),cagr=round((eq**(12/len(rets))-1)*100,1),max_dd=round(dd*100,1))
OUT['buy_and_hold']=bh
OUT['random_entries']={mk:orb['markets'][mk].get('random') for mk in ('NQ','ES') if orb['markets'].get(mk)}
# what different risk levels would have felt like (the sizing calculator)
X=SER['Portfolio']; B=block_boot(X,3000)
OUT['risk_levels']=[dict(risk=r,cagr=round(cagr(X,r),1),dd=round(grow(X,r)[1]*100,1),dd_bad=round(pct([grow(y,r)[1]*100 for y in B],.05),1),
                         p_halved=round(sum(1 for y in B if grow(y,r)[1]<=-0.5)/len(B),3)) for r in (0.25,0.5,1.0,2.0)]
json.dump(OUT,open(os.path.join(ROOT,'data','stats.json'),'w'),indent=1)
print(json.dumps(OUT['strategies']['Portfolio'],indent=0)[:600])
