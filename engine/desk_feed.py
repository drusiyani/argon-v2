"""Export the live desk's real calls for the 3D desk page (docs/desk_feed.json, served by GitHub Pages).
Only rewrites the file when the calls or results change, so the site isn't rebuilt every 5 minutes for nothing."""
import os,json,datetime as dt
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALLS=os.path.join(ROOT,'data','desk_calls.jsonl'); FARM=os.path.join(ROOT,'data','farm.json'); OUT=os.path.join(ROOT,'docs','desk_feed.json')
calls=[]
if os.path.exists(CALLS):
    for ln in open(CALLS):
        try: calls.append(json.loads(ln))
        except Exception: pass
res={}
if os.path.exists(FARM):
    try: res={t['key']:t.get('R') for t in json.load(open(FARM)).get('trades',[]) if t.get('route')=='feed' and t.get('key')}
    except Exception: pass
def clean(v): return dict(view=v.get('view') or v.get('decision'),confidence=v.get('confidence'),reason=(v.get('reason') or '')[:400])
rows=[dict(key=c['key'],when=c['when'],inst=c['inst'],setup=c['setup'],views={k:clean(v) for k,v in c.get('views',{}).items()},chief=clean(c.get('chief',{})),R=res.get(c['key'])) for c in calls][-40:]
done=[r for r in rows if r['R'] is not None]; took=[r for r in done if r['chief']['view']=='take']
score=dict(calls=len(calls),resolved=len(done),taken=len(took),taken_R=round(sum(r['R'] for r in took),2),all_R=round(sum(r['R'] for r in done),2))
dt_call=None; dp=os.path.join(ROOT,'data','daytype.jsonl')
if os.path.exists(dp):
    try:
        last=[json.loads(l) for l in open(dp) if l.strip()][-1]
        dt_call=dict(date=last['date'],made_at=last['made_at'],late=last['late'],ai=last['ai'],dumb_size=last['dumb_size'],ai_size_used=last['ai_size_used'],shadow=True,
                     inputs={k:last['inputs'].get(k) for k in ('vix','vix_1y_percentile','range_ratio','rsi5','overnight_change_pct','calendar')})
    except Exception: pass
ds=None; sp=os.path.join(ROOT,'data','daytype_score.json')
if os.path.exists(sp):
    try: x=json.load(open(sp)); ds=dict(scored_days=x['scored_days'],arms=x['arms'],verdict=x['verdict'],brier=x['ai_trend_brier'])
    except Exception: pass
feed=dict(source="Argon's original strategy (liquidity sweep → structure shift → fair value gap), NQ/ES/YM/RTY. The v2 book is not connected to the desk yet.",
          score=score,calls=rows[::-1],daytype=dt_call,daytype_score=ds)
old=json.load(open(OUT)) if os.path.exists(OUT) else None
if not old or {k:v for k,v in old.items() if k!='updated'}!=feed:
    feed['updated']=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'); json.dump(feed,open(OUT,'w'),indent=1); print('desk feed updated:',len(rows),'calls')
else: print('desk feed unchanged')
