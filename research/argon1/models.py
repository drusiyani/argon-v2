"""Argon-1 candidates.

A: Kronos-small, frozen, turns each symbol's last 256 five-minute bars into a 1,024-number summary (mean of its hidden
   states + the last one). PCA squeezes each symbol to 32 numbers (fitted on training days only), then a regularised
   logistic regression with the daily inputs gives the trend chance.
B: a tiny transformer trained from scratch on the same bars and daily inputs.
Baseline: logistic regression on the VIX 1-year percentile and yesterday's range ratio (the Amendment 9 idea, refitted
   on the training years so the comparison is like for like).
Nothing here is pickled: weights are saved as numbers (npz / torch state dicts) and loaded with the code below.
"""
import os, sys, math, json
import numpy as np

KRONOS_COMMIT = '67b630e67f6a18c9e9be918d9b4337c960db1e9a'
KRONOS_MODEL = 'NeoQuasar/Kronos-small'; KRONOS_TOK = 'NeoQuasar/Kronos-Tokenizer-base'
KRONOS_MODEL_REV = '901c26c1332695a2a8f243eb2f37243a37bea320'; KRONOS_TOK_REV = '0e0117387f39004a9016484a186a908917e22426'   # pinned weights
SEED = 7


# ------------------------------------------------------------------ metrics
def metrics(y, p):
    from sklearn.metrics import roc_auc_score
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6); y = np.asarray(y, float)
    ll = float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
    return dict(n=int(len(y)), base_rate=round(float(y.mean()), 4), logloss=round(ll, 5),
                brier=round(float(np.mean((p - y) ** 2)), 5), auc=round(float(roc_auc_score(y, p)), 4) if 0 < y.mean() < 1 else None)


# ------------------------------------------------------------------ standardise (fit on train only)
class Std:
    def fit(self, X): self.m = X.mean(0); self.s = X.std(0) + 1e-6; return self
    def __call__(self, X): return (X - self.m) / self.s
    def state(self): return dict(m=self.m, s=self.s)
    @classmethod
    def load(cls, d): o = cls(); o.m = d['m']; o.s = d['s']; return o


def logistic(X, y, C):
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(C=C, max_iter=5000).fit(X, y)


# ------------------------------------------------------------------ baseline
BASE_COLS = ('vix_pct', 'range_ratio')


# ------------------------------------------------------------------ A: Kronos embeddings
def kronos_load(vendor_dir):
    sys.path.insert(0, vendor_dir)
    from model import Kronos, KronosTokenizer
    tok = KronosTokenizer.from_pretrained(KRONOS_TOK, revision=KRONOS_TOK_REV); mdl = Kronos.from_pretrained(KRONOS_MODEL, revision=KRONOS_MODEL_REV)
    tok.eval(); mdl.eval(); return tok, mdl


def kronos_embed(raw, stamp, tok, mdl, batch=32):
    """raw (N,2,SEQ,6), stamp (N,2,SEQ,5) -> (N, 2, 1024): per symbol, mean and last of Kronos-small's hidden states.
    Each window is normalised on its own, exactly like Kronos' own predictor."""
    import torch
    N = raw.shape[0]; out = np.zeros((N, raw.shape[1], 1024), np.float32)
    with torch.no_grad():
        for s in range(raw.shape[1]):
            for i in range(0, N, batch):
                x = raw[i:i + batch, s].astype(np.float32)
                x = (x - x.mean(1, keepdims=True)) / (x.std(1, keepdims=True) + 1e-5); x = np.clip(x, -5, 5)
                xt = torch.from_numpy(x); st = torch.from_numpy(stamp[i:i + batch, s].astype(np.float32))
                s1, s2 = tok.encode(xt, half=True)
                _, h = mdl.decode_s1(s1, s2, st)
                out[i:i + batch, s] = torch.cat([h.mean(1), h[:, -1]], 1).numpy()
    return out


class PCA:
    def fit(self, X, k):
        self.mu = X.mean(0); U, S, Vt = np.linalg.svd(X - self.mu, full_matrices=False); self.W = Vt[:k].T; return self
    def __call__(self, X): return (X - self.mu) @ self.W
    def state(self): return dict(mu=self.mu, W=self.W)
    @classmethod
    def load(cls, d): o = cls(); o.mu = d['mu']; o.W = d['W']; return o


def a_features(emb, ctx, pcas):
    return np.concatenate([pcas[s](emb[:, s]) for s in range(emb.shape[1])] + [ctx], 1)


# ------------------------------------------------------------------ B: tiny transformer
def tiny_net(n_ctx, d=48, layers=2, heads=4, seq=256):
    import torch, torch.nn as nn

    class Tiny(nn.Module):
        def __init__(self):
            super().__init__()
            self.inp = nn.Linear(4, d); self.pos = nn.Parameter(torch.zeros(1, seq, d)); self.sym = nn.Parameter(torch.zeros(2, 1, d))
            enc = nn.TransformerEncoderLayer(d, heads, 2 * d, dropout=0.1, batch_first=True)
            self.enc = nn.TransformerEncoder(enc, layers)
            self.ctx = nn.Sequential(nn.Linear(n_ctx, d), nn.GELU())
            self.head = nn.Sequential(nn.Dropout(0.2), nn.Linear(3 * d, d), nn.GELU(), nn.Linear(d, 1))

        def forward(self, seqx, ctx):        # seqx (B,2,SEQ,4) scaled, ctx (B,n_ctx) standardised
            z = []
            for s in range(seqx.shape[1]):
                h = self.enc(self.inp(seqx[:, s]) + self.pos + self.sym[s]); z.append(h.mean(1))
            return self.head(torch.cat(z + [self.ctx(ctx)], 1)).squeeze(1)
    return Tiny()


SEQ_SCALE = np.array([1 / 0.15, 1 / 0.15, 1 / 0.15, 1.0], np.float32)   # 5-minute moves are ~0.1%: bring to ~1


def train_tiny(seq_tr, ctx_tr, y_tr, seq_va=None, ctx_va=None, y_va=None, epochs=80, patience=10, fixed_epochs=None, log=print):
    """Early stopping on validation log-loss (or a fixed number of epochs for the refit). Returns (model, best_epoch, history)."""
    import torch
    torch.manual_seed(SEED); np.random.seed(SEED); torch.set_num_threads(max(1, os.cpu_count() or 1))
    net = tiny_net(ctx_tr.shape[1]); opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=1e-2)
    lossf = torch.nn.BCEWithLogitsLoss()
    T = lambda a: torch.from_numpy(np.ascontiguousarray(a, np.float32))
    Xs, Xc, Y = T(seq_tr * SEQ_SCALE), T(ctx_tr), T(y_tr)
    best = (math.inf, 0, None); hist = []; n = len(Y); g = torch.Generator().manual_seed(SEED)
    for ep in range(1, (fixed_epochs or epochs) + 1):
        net.train(); perm = torch.randperm(n, generator=g)
        for i in range(0, n, 64):
            b = perm[i:i + 64]; opt.zero_grad(); l = lossf(net(Xs[b], Xc[b]), Y[b]); l.backward(); opt.step()
        if fixed_epochs: continue
        p = predict_tiny(net, seq_va, ctx_va); vl = metrics(y_va, p)['logloss']; hist.append((ep, vl)); log(f'  B epoch {ep}: val logloss {vl}')
        if vl < best[0]: best = (vl, ep, {k: v.clone() for k, v in net.state_dict().items()})
        elif ep - best[1] >= patience: break
    if not fixed_epochs: net.load_state_dict(best[2]); return net, best[1], hist
    return net, fixed_epochs, hist


def predict_tiny(net, seqx, ctx):
    import torch
    net.eval()
    with torch.no_grad():
        out = []
        for i in range(0, len(ctx), 256):
            out.append(torch.sigmoid(net(torch.from_numpy(np.ascontiguousarray(seqx[i:i + 256] * SEQ_SCALE, np.float32)),
                                         torch.from_numpy(np.ascontiguousarray(ctx[i:i + 256], np.float32)))).numpy())
    return np.concatenate(out) if out else np.zeros(0)
