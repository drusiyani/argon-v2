"""ORIGINAL deep-dive test from the old chat, saved as-is (only ROOT and the output path changed).
Deep dive: two documented intraday-momentum strategies on 5 years of real NQ and ES futures, Argon's honest way.
 A. Market intraday momentum (Gao, Han, Li & Zhou, JFE 2018): yesterday's close -> 10:00 return predicts 15:30 -> close.
 B. Noise-band momentum with a VWAP stop (Zarattini, Aziz & Barbon): trade breakouts of the usual move from the open.
Real costs, stop slippage, roll days skipped, monthly re-pick from the previous 6 months, random-direction baseline."""
import os,sys,gzip,csv,glob,json,collections,datetime as dt,random,statistics as stt,itertools
ROOT=os.environ.get('ARGON_ROOT',os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0,ROOT+'/engine')
from calendar_us import FOMC
from zoneinfo import ZoneInfo
NY=ZoneInfo('America/New_York'); COST={'NQ':0.75,'ES':0.5}; TICK={'NQ':0.25,'ES':0.25}
def load(s):
    days=collections.defaultdict(list); off={}; iid={}
    for f in sorted(glob.glob(f'{ROOT}/data/databento/{s}_*.csv.gz')):
        with gzip.open(f,'rt') as fh:
            r=csv.reader(fh); h=next(r); iv=h.index('volume'); ii=h.index('instrument_id')
            for row in r:
                ts=row[0]; d0=ts[:10]
                if d0 not in off: off[d0]=dt.datetime(int(d0[:4]),int(d0[5:7]),int(d0[8:10]),12,tzinfo=dt.timezone.utc).astimezone(NY).utcoffset().total_seconds()/60
                m=int(ts[11:13])*60+int(ts[14:16])+int(off[d0]); day=d0
                if m<0: m+=1440; day=(dt.date.fromisoformat(d0)-dt.timedelta(days=1)).isoformat()
                if 570<=m<960: days[day].append((m,float(row[4]),float(row[5]),float(row[6]),float(row[7]),float(row[iv]))); iid.setdefault(day,row[ii])
    days={d:list({x[0]:x for x in v}.values()) for d,v in days.items()}   # FIX: 2026-09 file overlaps 2026-partial; keep one bar per minute
    out={d:sorted(v) for d,v in days.items() if len(v)>=300 and sorted(v)[0][0]==570}
    keys=sorted(out); roll={b for a,b in zip(keys,keys[1:]) if iid[a]!=iid[b]}
    return out,roll
def at(rows,m):   # last candle that started before minute m
    k=None
    for x in rows:
        if x[0]<m: k=x
        else: break
    return k
RES={}
for s in os.environ.get('SYMS','NQ,ES').split(','):
    D,ROLL=load(s); K=sorted(D); A=collections.defaultdict(list); B=collections.defaultdict(list)
    for i,d in enumerate(K):
        if i<21 or d in ROLL: continue
        rows=D[d]; prev=D[K[i-1]]; pc=prev[-1][4]; op=rows[0][1]; month=d[:7]
        atr=stt.mean(max(x[2] for x in D[k])-min(x[3] for x in D[k]) for k in K[i-14:i])
        rg=random.Random(f'{s}{d}')
        # ---------- A: market intraday momentum
        c10=at(rows,600); c1530=at(rows,930); c15=at(rows,900)
        if c10 and c1530 and c15:
            r1=c10[4]/pc-1; r12=c1530[4]/c15[4]-1
            past=[]
            for k in K[i-20:i]:
                x=at(D[k],600)
                if x: past.append(abs(x[4]/D[K[K.index(k)-1]][-1][4]-1))
            vol_day=abs(r1)>stt.median(past) if past else False
            entry_bar=next((x for x in rows if x[0]>=930),None)
            if entry_bar:
                for sig in ('r1','r12','both'):
                    if sig=='r1': side=1 if r1>0 else -1
                    elif sig=='r12': side=1 if r12>0 else -1
                    else:
                        if (r1>0)!=(r12>0): continue
                        side=1 if r1>0 else -1
                    for stopk in ('none','atr'):
                        for filt in ('all','volatile'):
                            if filt=='volatile' and not vol_day: continue
                            for kind,sd_ in (('real',side),('rnd',rg.choice((1,-1)))):
                                entry=entry_bar[1]+sd_*TICK[s]; risk=0.15*atr; stop=entry-sd_*risk; res=None
                                for x in rows:
                                    if x[0]<930: continue
                                    if x[0]>=955: res=(x[4]-entry)*sd_; break
                                    if stopk=='atr' and ((x[3]<=stop) if sd_==1 else (x[2]>=stop)): res=(stop-sd_*TICK[s]-entry)*sd_; break
                                if res is None: res=(rows[-1][4]-entry)*sd_
                                (A if kind=='real' else A).setdefault((kind,sig,stopk,filt),[]).append((month,res/risk-COST[s]/risk,d))
        # ---------- B: noise-band momentum with VWAP
        sig_by_m=collections.defaultdict(list)
        for k in K[i-14:i]:
            r=D[k]; o=r[0][1]
            for x in r: sig_by_m[x[0]].append(abs(x[4]/o-1))
        hi_ref=max(op,pc); lo_ref=min(op,pc)
        for freq in (30,60):
            for mult in (1.0,1.5):
                for stopk in ('band','vwap'):
                    for kind in ('real','rnd'):
                        pos=0; ent=0; unit=0; pv=0; vv=0; trades=[]
                        for x in rows:
                            m,o,h,l,c,v=x; tp=(h+l+c)/3; pv+=tp*v; vv+=v; vwap=pv/vv if vv else c
                            if m>=955:
                                if pos: trades.append(((c-ent)*pos-COST[s])/unit)
                                pos=0; break
                            if m<600 or (m-570)%freq!=freq-1: continue   # decisions at the close of each half-hour (or hour) candle
                            sg=stt.mean(sig_by_m[m]) if sig_by_m[m] else None
                            if not sg: continue
                            up=hi_ref*(1+mult*sg); dn=lo_ref*(1-mult*sg)
                            if pos==1 and (c<up if stopk=='band' else c<max(up,vwap)) or pos==-1 and (c>dn if stopk=='band' else c>min(dn,vwap)):
                                trades.append(((c-pos*TICK[s]-ent)*pos-COST[s])/unit); pos=0
                            if pos==0 and m<=930 and (c>up or c<dn):
                                pos=1 if c>up else -1
                                if kind=='rnd': pos=rg.choice((1,-1))
                                ent=c+pos*TICK[s]; unit=max(1e-6,mult*sg*op)
                        if pos and rows: trades.append(((rows[-1][4]-ent)*pos-COST[s])/unit)
                        for tr in trades: B.setdefault((kind,freq,mult,stopk),[]).append((month,tr,d))
    RES[s]=(A,B)
def sharpe(x): mu=stt.mean(x); sd=stt.stdev(x); return mu/sd*12**.5 if sd>0 else 0
def wf(res,keys,months):
    mon={k:collections.defaultdict(float) for k in keys}; cnt={k:collections.Counter() for k in keys}
    for k in keys:
        for m,r,d in res.get(k,[]): mon[k][m]+=r; cnt[k][m]+=1
    ser=[];n=0
    for i,m in enumerate(months[6:],6):
        prev=months[i-6:i]; b=max(keys,key=lambda k:sum(mon[k][p] for p in prev)); ser.append(mon[b][m]); n+=cnt[b][m]
    return ser,n
def rep(ser,n):
    eq=pk=dd=0
    for x in ser: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    h=len(ser)//2; e=1
    for x in ser: e*=1+x*0.005
    return dict(trades=n,R=round(sum(ser),1),sharpe=round(sharpe(ser),2),dd=round(dd,1),halves=[round(sum(ser[:h]),1),round(sum(ser[h:]),1)],cagr=round((e**(12/len(ser))-1)*100,1))
OUT={}
for s in RES:
    A,B=RES[s]
    for nm,res in (('A_intraday_momentum',A),('B_noise_band',B)):
        months=sorted({m for v in res.values() for m,_,_ in v}); real=[k for k in res if k[0]=='real']; rnd=[k for k in res if k[0]=='rnd']
        rs,rn=wf(res,real,months); qs,qn=wf(res,rnd,months)
        OUT[f'{s} {nm}']=dict(real=rep(rs,rn),random=rep(qs,qn),monthly=dict(zip(months[6:],[round(x,3) for x in rs])),variants=len(real))
        print(s,nm,'real',OUT[f'{s} {nm}']['real'],'| random',OUT[f'{s} {nm}']['random'])
json.dump(OUT,open(ROOT+'/research/results/orig_deep_results.json','w'),indent=1)
