"""Strategies from published research and well-known traders, tested on the same 711 days, minute by minute.
  ORB:      Zarattini & Aziz, "Can Day Trading Really Be Profitable?" (SSRN 4416622): trade the direction of the first
            5-minute candle of the US session, stop at the other side of it, target 10x the risk or exit at the close.
  Momentum: in the spirit of Zarattini, Aziz & Barbon's intraday momentum work: only trade when price leaves its usual
            "noise" band around the open, checked every half hour, exit when it falls back inside or at the close.
"""
import os,json,collections,datetime as dt,bisect
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(ROOT,'engine','backtest_core.py')).read().split('# ---------------- swings & structure per tf')[0])
from zoneinfo import ZoneInfo
NYZ=ZoneInfo('America/New_York')
def by_day(s):
    T,O,H,L,C=M1[s]; days=collections.defaultdict(list); off={}
    for i in range(len(T)):
        t=int(T[i]); dk=t//86400
        if dk not in off:
            d=dt.datetime.fromtimestamp(t,NYZ); off[dk]=d.utcoffset().total_seconds()
        loc=int(t+off[dk]); ld=loc//86400; m=(loc%86400)//60
        if 570<=m<960: days[ld].append((m,O[i],H[i],L[i],C[i]))
    return days
import sys,random as _rnd
sys.path.insert(0,os.path.join(ROOT,'engine')); from calendar_us import FOMC,FOMC_EXIT_MIN
TICKS={'NQ':0.25,'ES':0.25,'YM':1.0,'RTY':0.1}
def walk(rows,start_idx,side,entry,stop,target,tick=0.25,exit_m=959):
    for m,o,h,l,c in rows[start_idx:]:
        if m>=exit_m: return (c-entry)*side
        if (l<=stop) if side==1 else (h>=stop): return (stop-side*(3 if m<585 else 1)*tick-entry)*side   # stops slip: 3 ticks in the first 15 minutes, 1 after
        if target is not None and ((h>=target) if side==1 else (l<=target)): return (target-entry)*side
    return (rows[-1][4]-entry)*side
OUT={}; BH={}
for s in ('NQ','ES'):
    D=by_day(s); keys=sorted(D); rng={}; res=collections.defaultdict(list)
    BH[s]={dt.date.fromordinal(dt.date(1970,1,1).toordinal()+k).strftime('%Y-%m'):D[k][-1][4] for k in keys if D[k]}   # last close of each month
    for k in keys:
        r=D[k]; rng[k]=max(x[2] for x in r)-min(x[3] for x in r)
    for idx,k in enumerate(keys):
        r=D[k]
        if len(r)<300 or r[0][0]!=570: continue
        day=dt.date.fromordinal(dt.date(1970,1,1).toordinal()+k); month=day.strftime('%Y-%m'); iso=day.isoformat()
        if iso in ROLL_DAYS.get(s,()): continue                     # contract roll day
        exit_m=FOMC_EXIT_MIN if iso in FOMC else 959                  # Fed day: flat before 2pm
        tk=TICKS[s]; rg=_rnd.Random(f'{s}{iso}')
        atr=sum(rng[x] for x in keys[max(0,idx-14):idx])/max(1,min(14,idx)) if idx else None
        closes=[D[x][-1][4] for x in keys[max(0,idx-20):idx] if D[x]]
        trend_up=(D[keys[idx-1]][-1][4]>sum(closes)/len(closes)) if len(closes)>=20 else None   # yesterday's close vs the 20-day average
        for orm in (5,15,30):
            first=[x for x in r if x[0]<570+orm]; rest_i=len(first)
            if rest_i>=len(r): continue
            o,c=first[0][1],first[-1][4]; h=max(x[2] for x in first); l=min(x[3] for x in first)
            if h<=l or abs(c-o)<0.05*(h-l): continue
            real_side=1 if c>o else -1; rand_side=rg.choice((1,-1))
            for kind,side in (('orb',real_side),('rnd',rand_side)):   # 'rnd' = same moment, random direction: the baseline to beat
              entry=r[rest_i][1]+side*(2*tk if r[rest_i][0]<585 else 0)   # entering at the open costs 2 extra ticks
              for stopk in ('candle','atr'):
                if stopk=='candle': stop=l if side==1 else h
                else:
                    if not atr: continue
                    stop=entry-side*0.10*atr
                risk=(entry-stop)*side
                if risk<=0: continue
                for tgt in ('10R','close'):
                    target=entry+side*10*risk if tgt=='10R' else None
                    pnl=walk(r,rest_i,side,entry,stop,target,tk,exit_m)
                    for filt in ('none','trend20'):
                        if filt=='trend20' and (trend_up is None or (side==1)!=trend_up): continue   # only trade with the 20-day trend
                        res[(kind,orm,stopk,tgt,filt)].append((month,pnl/risk,risk,iso))
        # noise-band momentum: dropped after the first test (it lost money on the Nasdaq)
        if False:
            op=r[0][1]; prevc=D[keys[idx-1]][-1][4]
            sig={}
            for kk in keys[idx-14:idx]:
                rr=D[kk]
                if not rr or rr[0][0]!=570: continue
                o0=rr[0][1]
                for m,_,_,_,cc in rr: sig.setdefault(m,[]).append(abs(cc/o0-1))
            pos=0; ent=0; unit=0
            for m,_,_,_,cc in r:
                if m<600 or (m-570)%30 or m>930:
                    if m>=959 and pos: res[('mom',)].append((month,(cc-ent)*pos/unit)); pos=0
                    continue
                sg=sum(sig.get(m,[0]))/max(1,len(sig.get(m,[1])))
                up=max(op,prevc)*(1+sg); dn=min(op,prevc)*(1-sg)
                if pos==1 and cc<up or pos==-1 and cc>dn:
                    res[('mom',)].append((month,(cc-ent)*pos/unit)); pos=0
                if pos==0 and (cc>up or cc<dn):
                    pos=1 if cc>up else -1; ent=cc; unit=max(1e-9,sg*op)
            if pos: res[('mom',)].append((month,(r[-1][4]-ent)*pos/unit))
    OUT[s]=res
COSTPTS={'NQ':0.75,'ES':0.5}   # one tick of slippage each way plus commission, in index points
def net(row,s): m,x,risk=row[:3]; return x-COSTPTS[s]/risk
def summ(rows):
    n=len(rows); R=sum(x for _,x in rows); w=sum(1 for _,x in rows if x>0); eq=pk=dd=0
    for _,x in sorted(rows): eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    return dict(n=n,R=round(R,1),avg=round(R/n,3) if n else 0,wr=round(w/n,3) if n else 0,dd=round(dd,1))
allkeys=sorted(set(k for s in OUT for k in OUT[s] if k[0]=='orb'),key=str); rkeys=sorted(set(k for s in OUT for k in OUT[s] if k[0]=='rnd'),key=str)
TAB={}
for k in allkeys:
    for mk in ('NQ','ES','both'):
        src=['NQ','ES'] if mk=='both' else [mk]
        rows=[(r[0],net(r,ss)) for ss in src for r in OUT[ss].get(k,[])]
        TAB[(k,mk)]=summ(rows)
for k in allkeys:
    print(str(k).ljust(34),'|'.join(f" {mk}: {TAB[(k,mk)]['n']:4d} tr {TAB[(k,mk)]['R']:+7.1f}R ({TAB[(k,mk)]['avg']:+.3f}/tr, win {round(100*TAB[(k,mk)]['wr'])}%, dd {TAB[(k,mk)]['dd']})" for mk in ('NQ','ES')))
# keep monthly series for the adaptive test and the site
json.dump({str(k)+'|'+s:[[r[0],round(net(r,s),3),round(r[2],2)] for r in OUT[s][k]] for s in OUT for k in OUT[s]},open(os.path.join(ROOT,'data','extra_trades.json'),'w'))
# honest version: every month, pick the ORB setting that did best over the previous 6 months, trade it next month
MONTHS=sorted(set(r[0] for s in OUT for k in OUT[s] for r in OUT[s][k]))
for mk in ('NQ','ES','both'):
    src=['NQ','ES'] if mk=='both' else [mk]
    mon={k:collections.defaultdict(float) for k in allkeys}; cnt={k:collections.defaultdict(int) for k in allkeys}
    for k in allkeys:
        for ss in src:
            for r in OUT[ss].get(k,[]): mon[k][r[0]]+=net(r,ss); cnt[k][r[0]]+=1
    tot=n=0; picks=[]; eq=pk=dd=0; up=0
    for i,m in enumerate(MONTHS[6:],6):
        prev=MONTHS[i-6:i]; best=max(allkeys,key=lambda k:sum(mon[k][p] for p in prev))
        tot+=mon[best][m]; n+=cnt[best][m]; picks.append(best); eq+=mon[best][m]; pk=max(pk,eq); dd=min(dd,eq-pk); up+=mon[best][m]>0
    print(f'ORB re-picked monthly, {mk}: {n} trades {tot:+.1f}R on {len(MONTHS)-6} unseen months, worst drop {dd:.1f}R, {up} months up, settings changed {sum(1 for a,b in zip(picks,picks[1:]) if a!=b)} times')
    pub=('orb',5,'candle','10R','none'); pr=[r for ss in src for r in OUT[ss].get(pub,[]) if r[0] in MONTHS[6:]]
    print(f'   published rule unchanged, same months: {len(pr)} trades {sum(net(r,ss) for ss in src for r in OUT[ss].get(pub,[]) if r[0] in MONTHS[6:]):+.1f}R')

# ---- what the site and the farm need
def keyname(k): return {'orm':k[1],'stop':k[2],'target':k[3],'filter':k[4]}
SUMMARY={'source':'Zarattini & Aziz, "Can Day Trading Really Be Profitable?" (SSRN 4416622)','months':len(MONTHS)-6,'markets':{}}
for mk in ('NQ','ES','both'):
    src=['NQ','ES'] if mk=='both' else [mk]
    mon={k:collections.defaultdict(float) for k in allkeys}; cnt={k:collections.defaultdict(int) for k in allkeys}; wins={k:collections.defaultdict(int) for k in allkeys}
    for k in allkeys:
        for ss in src:
            for r in OUT[ss].get(k,[]):
                x=net(r,ss); mon[k][r[0]]+=x; cnt[k][r[0]]+=1; wins[k][r[0]]+=x>0
    tot=n=0; eq=pk=dd=0; up=0; curve=[]; series=[]; trades=[]
    for i,m in enumerate(MONTHS[6:],6):
        prev=MONTHS[i-6:i]; best=max(allkeys,key=lambda k:sum(mon[k][p] for p in prev))
        tot+=mon[best][m]; n+=cnt[best][m]; eq+=mon[best][m]; pk=max(pk,eq); dd=min(dd,eq-pk); up+=mon[best][m]>0; curve.append([m,round(eq,2)]); series.append([m,round(mon[best][m],2),cnt[best][m],wins[best][m]])
        if mk!='both': trades+=[[r[3],round(net(r,mk),3),round(r[2],2)] for r in OUT[mk].get(best,[]) if r[0]==m]
    now=max(allkeys,key=lambda k:sum(mon[k][p] for p in MONTHS[-6:]))
    pub=('orb',5,'candle','10R','none'); pr=[(r[0],net(r,ss)) for ss in src for r in OUT[ss].get(pub,[]) if r[0] in MONTHS[6:]]
    mr=[]; pv=0
    for _m,_v in curve: mr.append(_v-pv); pv=_v
    _mu=sum(mr)/len(mr) if mr else 0; _sd=(sum((x-_mu)**2 for x in mr)/(len(mr)-1))**.5 if len(mr)>2 else 0
    fan=[]
    for k in allkeys:
        t=0; c=[]
        for m in MONTHS[6:]: t+=mon[k][m]; c.append(round(t,1))
        fan.append(c)
    rmon=collections.defaultdict(lambda:collections.defaultdict(float))
    for k in rkeys:
        for ss in src:
            for r in OUT[ss].get(k,[]): rmon[k][r[0]]+=net(r,ss)
    rser=[]
    for i,m in enumerate(MONTHS[6:],6):
        prev=MONTHS[i-6:i]; b=max(rkeys,key=lambda k:sum(rmon[k][p] for p in prev)); rser.append(rmon[b][m])
    _rm=sum(rser)/len(rser); _rs=(sum((x-_rm)**2 for x in rser)/(len(rser)-1))**.5
    SUMMARY['markets'][mk]=dict(random=dict(R=round(sum(rser),1),sharpe=round(_rm/_rs*12**.5,2) if _rs>0 else 0.0),trades=trades,series=series,sharpe=round(_mu/_sd*12**.5,2) if _sd>0 else 0.0,fan=fan,adaptive=dict(n=n,R=round(tot,1),dd=round(dd,1),up=up),published=summ(pr),now=keyname(now),now_last6=round(sum(mon[now][p] for p in MONTHS[-6:]),1),curve=curve)
SUMMARY['bh']={s:{m:c for m,c in BH[s].items()} for s in BH}
json.dump(SUMMARY,open(os.path.join(ROOT,'data','orb_out.json'),'w'))
print('ORB now:',{mk:SUMMARY['markets'][mk]['now'] for mk in SUMMARY['markets']})
