"""Every sweep setup from the long test with exact times, so the mistake book never uses a result before it was known."""
import os,json
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(ROOT,'engine','backtest_core.py')).read())
rows=[]
for c in CANDS:
    sw=c['sw']; p=c['p']; sm=c['sims'].get(('ob','2R')) or c['sims'].get(('fvg','2R'))
    if not (sm and sm.get('fill') is not None and c['m'] and c['m']['disp'] and sw['cls']!='acceptance'): continue
    rows.append(dict(inst=c['s'],day=str(sw['sd']),hour=c['hour'],dow=c['dow'],session=sw['win'],level=p['name'],level_kind=p['kind'],level_tf=p['tf'],sweep=sw['cls'],smt=int(bool(sw['smt'])),h1=int(c['h1']),
        decide_t=c['m']['t']+300,fill_t=sm['fill_t'],exit_t=sm['exit_t'],R=sm['R']))
json.dump(rows,open(os.path.join(ROOT,'data','setups_timed.json'),'w'))
print('timed setups',len(rows))
