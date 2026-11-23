"""Argon-1 training, one stage at a time (each stage saves its output, so a failed or timed-out job resumes from the last one).

  python research/argon1/train.py features          # bars -> features.npz
  python research/argon1/train.py embed             # Kronos-small summaries -> kronos_emb.npz (the slow step)
  python research/argon1/train.py select            # fit baseline, A, B on 2011-2020; choose on 2021-2023
  python research/argon1/train.py test              # ONCE: score the choice on Jan 2024 - Oct 2026
  python research/argon1/train.py refit --version argon1 --end 2026-10-31   # fit the choice on everything, freeze

Private files (features, embeddings, weights) go to $ARGON1_DIR (inside the private data repo on the runner).
Only metrics and fingerprints are written to research/results/ in the public repo.
"""
import os, sys, json, hashlib, argparse, datetime as dt
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from argon1 import data as D, models as M

ROOT = D.ROOT
PUB = os.path.join(ROOT, 'research', 'results')
TRAIN = ('2011-01-01', '2020-12-31'); VAL = ('2021-01-01', '2023-12-31'); TEST = ('2024-01-01', '2026-10-31')
C_GRID = (0.003, 0.01, 0.03, 0.1, 0.3, 1.0)
PCA_K = 32
RAW = os.environ.get('ARGON1_RAW', '/tmp/argon1_raw.npz')


def priv(name): d = os.environ.get('ARGON1_DIR', os.path.join(ROOT, 'data', 'argon1')); os.makedirs(d, exist_ok=True); return os.path.join(d, name)
def sha(path): return hashlib.sha256(open(path, 'rb').read()).hexdigest()
def wpub(name, obj):
    os.makedirs(PUB, exist_ok=True); json.dump(obj, open(os.path.join(PUB, name), 'w'), indent=1, default=str); print('wrote', name)
def now(): return dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ')


def load():
    F = dict(np.load(priv('features.npz'), allow_pickle=False))
    E = priv('kronos_emb.npz'); F['emb'] = np.load(E)['emb'] if os.path.exists(E) else None
    return F


def mask(F, a, b): return (F['dates'] >= a) & (F['dates'] <= b) & F['ok']


def ctx_cols(names): return [D.CTX_FEATS.index(n) for n in names]


# ------------------------------------------------------------------ stages
def features():
    bars = {s: D.five_minute(D.read_minutes(s)) for s in D.SYMS}
    out = D.build(bars, D.vix_history())
    raw = dict(raw=out.pop('raw'), stamp=out.pop('stamp'), dates=out['dates'])
    np.savez_compressed(RAW, **raw)                  # ~150 MB: kept on the runner only (too big for git; rebuilt when needed)
    np.savez_compressed(priv('features.npz'), **out)
    y = out['y'][out['ok']]
    wpub('argon1_features.json', dict(made=now(), days=int(len(out['dates'])), labelled=int(out['ok'].sum()),
         first=str(out['dates'][0]), last=str(out['dates'][-1]), trend_rate=round(float(y.mean()), 4),
         sequence=[f'{s}:{f}' for s in D.SYMS for f in D.SEQ_FEATS], daily=list(D.CTX_FEATS), bars=D.SEQ, cutoff='08:45 New York'))


def embed():
    if not os.path.exists(RAW): features()
    F = dict(np.load(RAW, allow_pickle=False))
    tok, mdl = M.kronos_load(os.environ.get('KRONOS_DIR', os.path.join(ROOT, 'vendor', 'Kronos')))
    emb = M.kronos_embed(F['raw'], F['stamp'], tok, mdl)
    np.savez_compressed(priv('kronos_emb.npz'), emb=emb, dates=F['dates'])
    print('embedded', emb.shape)


def fit_all(F, tr, ev, C=None, epochs=None, log=print):
    """Fit baseline, A and B on rows `tr`; return predictions on rows `ev` and the fitted parts."""
    y = F['y']; ctx = F['ctx']; std = M.Std().fit(ctx[tr]); res = {}
    bc = ctx_cols(M.BASE_COLS); bstd = M.Std().fit(ctx[tr][:, bc])
    base = M.logistic(bstd(ctx[tr][:, bc]), y[tr], C=1e6)
    res['baseline'] = dict(p=base.predict_proba(bstd(ctx[ev][:, bc]))[:, 1], parts=dict(std=bstd, lr=base))
    if F['emb'] is not None:
        pcas = [M.PCA().fit(F['emb'][tr][:, s], PCA_K) for s in range(F['emb'].shape[1])]
        Xtr = M.a_features(F['emb'][tr], std(ctx[tr]), pcas); Xev = M.a_features(F['emb'][ev], std(ctx[ev]), pcas)
        xs = M.Std().fit(Xtr)
        grid = [C] if C else C_GRID; best = None
        for c in grid:
            lr = M.logistic(xs(Xtr), y[tr], c); p = lr.predict_proba(xs(Xev))[:, 1]; ll = M.metrics(y[ev], p)['logloss']
            log(f'  A C={c}: logloss {ll}')
            if best is None or ll < best[0]: best = (ll, c, lr, p)
        res['A'] = dict(p=best[3], C=best[1], parts=dict(pcas=pcas, std=std, xs=xs, lr=best[2]))
    net, ep, hist = M.train_tiny(F['seq'][tr], std(ctx[tr]), y[tr], F['seq'][ev], std(ctx[ev]), y[ev], log=log) if not epochs else \
        M.train_tiny(F['seq'][tr], std(ctx[tr]), y[tr], fixed_epochs=epochs, log=log)
    res['B'] = dict(p=M.predict_tiny(net, F['seq'][ev], std(ctx[ev])), epochs=ep, parts=dict(net=net, std=std), hist=hist)
    return res


def select():
    F = load(); tr = mask(F, *TRAIN); va = mask(F, *VAL)
    res = fit_all(F, tr, va)
    m = {k: M.metrics(F['y'][va], v['p']) for k, v in res.items()}
    cands = [k for k in ('A', 'B') if k in m]
    pick = min(cands, key=lambda k: m[k]['logloss'])
    passed = m[pick]['logloss'] < m['baseline']['logloss']
    sel = dict(made=now(), rule='lower validation log-loss of A and B; must beat the baseline, else chosen anyway and flagged',
               train=TRAIN, validate=VAL, n_train=int(tr.sum()), n_val=int(va.sum()), metrics=m, chosen=pick,
               beat_baseline_on_validation=bool(passed), A_C=res.get('A', {}).get('C'), B_epochs=res['B']['epochs'],
               pca_k=PCA_K, seed=M.SEED, kronos=dict(model=M.KRONOS_MODEL, model_rev=M.KRONOS_MODEL_REV, tokenizer=M.KRONOS_TOK, tokenizer_rev=M.KRONOS_TOK_REV, commit=M.KRONOS_COMMIT))
    json.dump(sel, open(priv('select.json'), 'w'), indent=1); wpub('argon1_select.json', sel)


def test():
    marker = os.path.join(PUB, 'argon1_test.json')
    if os.path.exists(marker): sys.exit('the test period has already been opened once; refusing to open it again')
    sel = json.load(open(priv('select.json'))); F = load(); tr = mask(F, *TRAIN); te = mask(F, *TEST)
    res = fit_all(F, tr, te, C=sel['A_C'], epochs=sel['B_epochs'])
    m = {k: M.metrics(F['y'][te], v['p']) for k, v in res.items()}
    wpub('argon1_test.json', dict(made=now(), opened_once=True, test=TEST, n_test=int(te.sum()), chosen=sel['chosen'],
         metrics=m, note='Fitted on 2011-2020 with the validation settings; reported whatever it says. Not used to change anything.'))


def valpreds():
    """Daily trend chances and sizes for the validation years (2021-2023) from the chosen model fitted on 2011-2020,
    for comparing books (plain / G3 / Argon-1 sizing). Never touches the test years."""
    sel = json.load(open(priv('select.json'))); F = load(); tr = mask(F, *TRAIN)
    va = (F['dates'] >= VAL[0]) & (F['dates'] <= VAL[1])          # every day, labelled or not (it trades every day)
    res = fit_all(F, tr, np.concatenate([np.where(tr)[0], np.where(va)[0]]), C=sel['A_C'], epochs=sel['B_epochs'])
    p = res[sel['chosen']]['p']; ptr, pva = p[:tr.sum()], p[tr.sum():]
    q = np.quantile(ptr, [0.25, 0.65, 0.85])
    size = lambda x: 2.0 if x >= q[2] else 1.5 if x >= q[1] else 0.5 if x < q[0] else 1.0
    wpub('argon1_val_preds.json', dict(made=now(), model=sel['chosen'], fitted_on=TRAIN, cutoffs=[round(float(v), 4) for v in q],
         days={str(d): [round(float(x), 4), size(x)] for d, x in zip(F['dates'][va], pva)}))


def refit(version, end):
    sel = json.load(open(priv('select.json'))); F = load(); al = mask(F, TRAIN[0], end)
    res = fit_all(F, al, al, C=sel['A_C'], epochs=sel['B_epochs'])
    k = sel['chosen']; d = priv(version); os.makedirs(d, exist_ok=True); files = {}
    if k == 'A':
        P = res['A']['parts']
        np.savez(os.path.join(d, 'model_a.npz'), **{f'pca{s}_{n}': v for s, p in enumerate(P['pcas']) for n, v in p.state().items()},
                 ctx_m=P['std'].m, ctx_s=P['std'].s, xs_m=P['xs'].m, xs_s=P['xs'].s, coef=P['lr'].coef_, intercept=P['lr'].intercept_)
        files['model_a.npz'] = None
    else:
        import torch
        P = res['B']['parts']; torch.save(P['net'].state_dict(), os.path.join(d, 'model_b.pt'))
        np.savez(os.path.join(d, 'ctx_std.npz'), m=P['std'].m, s=P['std'].s); files['model_b.pt'] = None; files['ctx_std.npz'] = None
    for f in files: files[f] = sha(os.path.join(d, f))
    q = np.quantile(res[k]['p'], [0.25, 0.65, 0.85])          # same size rule as the market forecaster (Amendment 9)
    cut = dict(half=round(float(q[0]), 4), one_and_half=round(float(q[1]), 4), two=round(float(q[2]), 4))
    meta = dict(version=version, made=now(), chosen=k, fitted_on=[TRAIN[0], end], n_days=int(al.sum()), A_C=sel['A_C'],
                B_epochs=sel['B_epochs'], pca_k=PCA_K, seed=M.SEED, files=files, cutoffs=cut,
                size_rule='p >= two -> 2x; p >= one_and_half -> 1.5x; p < half -> 0.5x; else 1x', features=list(D.CTX_FEATS), bars=D.SEQ,
                kronos=dict(model=M.KRONOS_MODEL, model_rev=M.KRONOS_MODEL_REV, tokenizer=M.KRONOS_TOK, tokenizer_rev=M.KRONOS_TOK_REV, commit=M.KRONOS_COMMIT))
    json.dump(meta, open(os.path.join(d, 'meta.json'), 'w'), indent=1)
    wpub(f'{version}_frozen.json', meta)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('stage'); ap.add_argument('--version', default='argon1'); ap.add_argument('--end', default=TEST[1])
    a = ap.parse_args()
    dict(features=features, embed=embed, select=select, test=test, valpreds=valpreds)[a.stage]() if a.stage != 'refit' else refit(a.version, a.end)
