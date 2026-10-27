"""ORIGINAL QuantLab test from the old chat, saved as-is (only ROOT and the output path changed).
@thequantbuilder's rule, tested Argon's way. First 5-minute candle of the US session (9:30-9:35 New York): close
above the 12 EMA (5-minute chart) -> long, below -> short. Enter at 9:35, trail the stop. Real futures, real costs."""
import os,sys,json,collections,datetime as dt,math,random,statistics as stt
ROOT=os.environ.get('ARGON_ROOT',os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0,ROOT+'/engine')
src=open(ROOT+'/engine/backtest_core.py').read().split('# ---------------- swings & structure per tf')[0]
g={'__file__':ROOT+'/engine/x.py'}; exec(src,g); M1=g['M1']; ROLL=g['ROLL_DAYS']
from calendar_us import FOMC,FOMC_EXIT_MIN
from zoneinfo import ZoneInfo
NY=ZoneInfo('America/New_York'); COST={'NQ':0.75,'ES':0.5}; TICK={'NQ':0.25,'ES':0.25}
VARIANTS=[(st,tr) for st in ('candle','atr') for tr in ('ema','chand2','chand3')]
def run(s):
    T,O,H,L,C=M1[s]; n=len(T); off={}; mins=[0]*n; days=['']*n
    for i in range(n):
        t=int(T[i]); dk=t//86400
        if dk not in off: off[dk]=dt.datetime.fromtimestamp(t,NY).utcoffset().total_seconds()
        loc=t+int(off[dk]); mins[i]=(loc%86400)//60; days[i]=dt.date.fromordinal(dt.date(1970,1,1).toordinal()+loc//86400).isoformat()
    # 5-minute bars over the whole session, and the 12 EMA on their closes
    b5=[]; cur=None
    for i in range(n):
        k=int(T[i])//300
        if cur is None or k!=cur[0]: cur=[k,i,i,O[i],H[i],L[i],C[i]]; b5.append(cur)
        else: cur[2]=i; cur[4]=max(cur[4],H[i]); cur[5]=min(cur[5],L[i]); cur[6]=C[i]
    ema=[]; e=None; a=2/13
    for b in b5: e=b[6] if e is None else e+a*(b[6]-e); ema.append(e)
    atr5=[]; q=collections.deque(maxlen=14)
    for b in b5: q.append(b[4]-b[5]); atr5.append(sum(q)/len(q))
    # daily regular-session range for the ATR stop
    rng={}; 
    for b in b5:
        i=b[1]
        if 570<=mins[i]<960: d=days[i]; lo,hi=rng.get(d,(1e18,-1e18)); rng[d]=(min(lo,b[5]),max(hi,b[4]))
    dlist=sorted(rng); datr={d:(sum(rng[x][1]-rng[x][0] for x in dlist[max(0,j-14):j])/min(14,j) if j else None) for j,d in enumerate(dlist)}
    out=collections.defaultdict(list); rnd=collections.defaultdict(list)
    first=[j for j,b in enumerate(b5) if mins[b[1]]==570]
    for j in first:
        b=b5[j]; d=days[b[1]]
        if d in ROLL.get(s,()) or not datr.get(d) or j+1>=len(b5) or mins[b5[j+1][1]]!=575: continue
        exit_m=FOMC_EXIT_MIN if d in FOMC else 955
        real=1 if b[6]>ema[j] else -1; rside=random.Random(f'{s}{d}').choice((1,-1))
        for kind,side in (('real',real),('rnd',rside)):
            entry0=O[b5[j+1][1]]; entry=entry0+side*2*TICK[s]          # market order at 9:35, 2 extra ticks at the open
            for vi,(stk,trk) in enumerate(VARIANTS):
                stop=(b[5] if side==1 else b[4]) if stk=='candle' else entry-side*0.10*datr[d]
                risk=(entry-stop)*side
                if risk<=0: continue
                stp=stop; best=entry; res=None
                for jj in range(j+1,len(b5)):
                    bb=b5[jj]
                    if days[bb[1]]!=d: break
                    for i in range(bb[1],bb[2]+1):
                        m=mins[i]
                        if m>=exit_m: res=(C[i]-entry)*side; break
                        if (L[i]<=stp) if side==1 else (H[i]>=stp): res=(stp-side*(3 if m<585 else 1)*TICK[s]-entry)*side; break
                    if res is not None: break
                    # the bar closed: move the trailing stop (never backwards)
                    best=max(best,bb[4]) if side==1 else min(best,bb[5])
                    if trk=='ema':
                        if (bb[6]<ema[jj]) if side==1 else (bb[6]>ema[jj]):
                            nxt=bb[2]+1; res=((O[nxt] if nxt<n else bb[6])-side*TICK[s]-entry)*side; break
                    else:
                        k=2 if trk=='chand2' else 3; ts=best-side*k*atr5[jj]
                        stp=max(stp,ts) if side==1 else min(stp,ts)
                if res is None: continue
                (out if kind=='real' else rnd)[vi].append((d[:7],res/risk-COST[s]/risk,d))
    return out,rnd
def sharpe(x): mu=stt.mean(x); sd=stt.stdev(x); return mu/sd*12**.5 if sd>0 else 0
def wf(res,months,look=6):
    mon={v:collections.defaultdict(float) for v in range(len(VARIANTS))}; cnt={v:collections.Counter() for v in range(len(VARIANTS))}; trades=[]
    for v,rows in res.items():
        for m,r,d in rows: mon[v][m]+=r; cnt[v][m]+=1
    ser=[]; n=0
    for i,m in enumerate(months[look:],look):
        prev=months[i-look:i]; bst=max(range(len(VARIANTS)),key=lambda v:sum(mon[v][p] for p in prev))
        ser.append(mon[bst][m]); n+=cnt[bst][m]; trades+=[r for mm,r,d in res.get(bst,[]) if mm==m]
    return ser,n,trades
def report(name,ser,n,trades):
    eq=pk=dd=0
    for x in ser: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    w=[t for t in trades if t>0]; l=[t for t in trades if t<=0]; pf=sum(w)/abs(sum(l)) if l else 0; h=len(ser)//2
    e=1
    for x in ser: e*=1+x*0.005
    return dict(name=name,trades=n,R=round(sum(ser),1),sharpe=round(sharpe(ser),2),max_dd=round(dd,1),win=round(100*len(w)/max(1,len(trades)),1),profit_factor=round(pf,2),
                first_half=round(sum(ser[:h]),1),second_half=round(sum(ser[h:]),1),cagr_at_0_5pct=round((e**(12/len(ser))-1)*100,1))
R={}
for s in ('NQ','ES'):
    out,rnd=run(s); months=sorted({m for rows in out.values() for m,_,_ in rows})
    ser,n,tr=wf(out,months); R[s]=report(f'{s} their rule, re-picked monthly',ser,n,tr)
    rs,rn,rt=wf(rnd,months); R[s+'_random']=report(f'{s} random direction, same moments',rs,rn,rt)
    fixed=(0,0)  # the most literal reading: stop at the first candle, exit when a 5-minute close crosses the EMA
    fv=VARIANTS.index(('candle','ema')); fr=[r for m,r,d in out[fv] if m>=months[6]]; fm=collections.defaultdict(float)
    for m,r,d in out[fv]:
        if m>=months[6]: fm[m]+=r
    R[s+'_literal']=report(f'{s} literal version (candle stop, EMA trail), fixed',[fm.get(m,0) for m in months[6:]],len(fr),fr)
    for k in (s,s+'_random',s+'_literal'): print(json.dumps(R[k]))
json.dump(R,open(ROOT+'/research/results/orig_qb_results.json','w'),indent=1)
