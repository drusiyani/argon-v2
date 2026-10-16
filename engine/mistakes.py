"""The mistake book. Every losing setup is tagged with what was wrong with it, using only what was known before the trade.
Each month, mistakes that kept costing money over the previous 6 months (in both halves, with enough examples) become
"avoid" rules for the next month. Tested honestly: the rules for a month are learned only from the months before it."""
import os,json,collections
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S=json.load(open(os.path.join(ROOT,'data','setups_timed.json')))
for c in S: c['R_2R']=c['R']
S.sort(key=lambda c:c['decide_t']); byday=collections.defaultdict(list)
for c in S: byday[c['day']].append(c)
for c in S:
    earlier=[x for x in byday[c['day']] if x['decide_t']<c['decide_t']]
    c['after_loss']=any(x['exit_t']<=c['decide_t'] and x['R']<0 for x in earlier)   # only losses that had already finished
    c['nth']=sum(1 for x in earlier if x['fill_t']<=c['decide_t'])
    c['daily']=None
TAGS={
 'against_hourly_trend':('traded against the hourly trend',lambda c:not c['h1']),
 'minor_level':('swept only a small 5-minute high or low',lambda c:c['level_tf']=='5m' and c['level_kind']=='swing'),
 'no_smt':('the other market followed (no SMT)',lambda c:not c['smt']),
 'slow_snapback':('price took a while to come back',lambda c:c['sweep']=='delayed'),
 'news_hour':('traded in the 8:30am news hour',lambda c:c['hour']==8),
 'late_in_session':('traded late in the session',lambda c:c['hour'] in (4,11)),
 'after_a_loss':('traded again after a loss that day',lambda c:c['after_loss']),
 'third_plus_trade':('third or later trade of the day',lambda c:c['nth']>=2),
 'friday':('traded on a Friday',lambda c:c['dow']==4),
}
for c in S: c['tags']=[k for k,(_,f) in TAGS.items() if f(c)]
MONTHS=sorted(set(c['day'][:7] for c in S)); LOOK=6; MINN=40; COST=0.05
def avg(xs): return sum(x['R_2R']-COST for x in xs)/len(xs) if xs else 0
def learn(rows):
    h=len(rows)//2; A,B=rows[:h],rows[h:]; rules=[]
    for k in TAGS:
        w=[c for c in rows if k in c['tags']]; wo=[c for c in rows if k not in c['tags']]
        if len(w)<MINN: continue
        wa=[c for c in A if k in c['tags']]; wb=[c for c in B if k in c['tags']]
        if avg(w)<-0.1 and avg(w)<avg(wo)-0.15 and avg(wa)<0 and avg(wb)<0: rules.append(k)
    return rules
res={'all':[], 'learned':[]}; log=[]
for i,m in enumerate(MONTHS):
    if i<LOOK: continue
    prev=[c for c in S if c['day'][:7] in MONTHS[i-LOOK:i]]; rules=learn(prev); cur=[c for c in S if c['day'][:7]==m]
    kept=[c for c in cur if not any(t in rules for t in c['tags'])]
    res['all'].append(sum(c['R_2R']-COST for c in cur)); res['learned'].append(sum(c['R_2R']-COST for c in kept))
    log.append(dict(month=m,rules=rules,all_n=len(cur),all_R=round(res['all'][-1],2),kept_n=len(kept),kept_R=round(res['learned'][-1],2)))
def dd(xs):
    eq=pk=d_=0
    for x in xs: eq+=x; pk=max(pk,eq); d_=min(d_,eq-pk)
    return round(d_,1)
book=[]
for k,(lab,_) in TAGS.items():
    w=[c for c in S if k in c['tags']]; wo=[c for c in S if k not in c['tags']]; losses=[c for c in w if c['R_2R']<0]
    book.append(dict(tag=k,label=lab,n=len(w),losses=len(losses),cost=round(sum(c['R_2R']-COST for c in losses),1),avg_with=round(avg(w),3),avg_without=round(avg(wo),3)))
book.sort(key=lambda b:b['avg_with']-b['avg_without'])
now=learn([c for c in S if c['day'][:7] in MONTHS[-LOOK:]])
OUT=dict(tags={k:v[0] for k,v in TAGS.items()},book=book,log=log,now=now,test=dict(months=len(log),all=dict(R=round(sum(res['all']),1),dd=dd(res['all']),up=sum(1 for x in res['all'] if x>0)),learned=dict(R=round(sum(res['learned']),1),dd=dd(res['learned']),up=sum(1 for x in res['learned'] if x>0))),
 rule_counts=collections.Counter(r for l in log for r in l['rules']))
json.dump(OUT,open(os.path.join(ROOT,'data','mistakes.json'),'w'),indent=1)
print('unseen months:',len(log),'| take every setup:',OUT['test']['all'],'| after learning from mistakes:',OUT['test']['learned'])
print('rules used (months):',dict(OUT['rule_counts']))
print('rules for next month:',now)
for b in book[:6]: print(f"  {b['label']:45s} n={b['n']:4d} avg {b['avg_with']:+.3f} vs {b['avg_without']:+.3f} without")
