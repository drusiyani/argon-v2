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
def walk(rows,start_idx,side,entry,stop,target):
    for m,o,h,l,c in rows[start_idx:]:
        if m>=959: return (c-entry)*side
        if (l<=stop) if side==1 else (h>=stop): return (stop-entry)*side
        if target is not None and ((h>=target) if side==1 else (l<=target)): return (target-entry)*side
    return (rows[-1][4]-entry)*side
OUT={}
for s in ('NQ','ES'):
    D=by_day(s); keys=sorted(D); rng={}; res=collections.defaultdict(list)
    for k in keys:
        r=D[k]; rng[k]=max(x[2] for x in r)-min(x[3] for x in r)
    for idx,k in enumerate(keys):
        r=D[k]
        if len(r)<300 or r[0][0]!=570: continue
        month=dt.date.fromordinal(dt.date(1970,1,1).toordinal()+k).strftime('%Y-%m')
        atr=sum(rng[x] for x in keys[max(0,idx-14):idx])/max(1,min(14,idx)) if idx else None
        closes=[D[x][-1][4] for x in keys[max(0,idx-20):idx] if D[x]]
        trend_up=(D[keys[idx-1]][-1][4]>sum(closes)/len(closes)) if len(closes)>=20 else None   # yesterday's close vs the 20-day average
        for orm in (5,15,30):
            first=[x for x in r if x[0]<570+orm]; rest_i=len(first)
            if rest_i>=len(r): continue
            o,c=first[0][1],first[-1][4]; h=max(x[2] for x in first); l=min(x[3] for x in first)
            if h<=l or abs(c-o)<0.05*(h-l): continue
            side=1 if c>o else -1; entry=r[rest_i][1]
            for stopk in ('candle','atr'):
                if stopk=='candle': stop=l if side==1 else h
                else:
                    if not atr: continue
                    stop=entry-side*0.10*atr
                risk=(entry-stop)*side
                if risk<=0: continue
                for tgt in ('10R','close'):
                    target=entry+side*10*risk if tgt=='10R' else None
                    pnl=walk(r,rest_i,side,entry,stop,target)
                    for filt in ('none','trend20'):
                        if filt=='trend20' and (trend_up is None or (side==1)!=trend_up): continue   # only trade with the 20-day trend
                        res[('orb',orm,stopk,tgt,filt)].append((month,pnl/risk,risk))
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
def net(row,s): m,x,risk=row; return x-COSTPTS[s]/risk
def summ(rows):
    n=len(rows); R=sum(x for _,x in rows); w=sum(1 for _,x in rows if x>0); eq=pk=dd=0
    for _,x in sorted(rows): eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    return dict(n=n,R=round(R,1),avg=round(R/n,3) if n else 0,wr=round(w/n,3) if n else 0,dd=round(dd,1))
allkeys=sorted(set(k for s in OUT for k in OUT[s]),key=str)
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
    mon={k:collections.defaultdict(float) for k in allkeys}; cnt={k:collections.defaultdict(int) for k in allkeys}
    for k in allkeys:
        for ss in src:
            for r in OUT[ss].get(k,[]): mon[k][r[0]]+=net(r,ss); cnt[k][r[0]]+=1
    tot=n=0; eq=pk=dd=0; up=0; curve=[]
    for i,m in enumerate(MONTHS[6:],6):
        prev=MONTHS[i-6:i]; best=max(allkeys,key=lambda k:sum(mon[k][p] for p in prev))
        tot+=mon[best][m]; n+=cnt[best][m]; eq+=mon[best][m]; pk=max(pk,eq); dd=min(dd,eq-pk); up+=mon[best][m]>0; curve.append([m,round(eq,2)])
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
    SUMMARY['markets'][mk]=dict(sharpe=round(_mu/_sd*12**.5,2) if _sd>0 else 0.0,fan=fan,adaptive=dict(n=n,R=round(tot,1),dd=round(dd,1),up=up),published=summ(pr),now=keyname(now),now_last6=round(sum(mon[now][p] for p in MONTHS[-6:]),1),curve=curve)
json.dump(SUMMARY,open(os.path.join(ROOT,'data','orb_out.json'),'w'))
print('ORB now:',{mk:SUMMARY['markets'][mk]['now'] for mk in SUMMARY['markets']})
