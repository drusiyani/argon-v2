"""Build the front page (docs/index.html) from Argon's own data: one honest story, top to bottom.
The old all-in-one dashboard is still built, as docs/lab.html, and linked from "What failed" and the footer."""
import os, json, html, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def J(*p, default=None):
    f = os.path.join(ROOT, *p)
    try: return json.load(open(f))
    except Exception: return default
P = J('data', 'portfolio.json', default={}); A = J('research', 'results', 'cards_databento.json', default={}); B = J('research', 'results', 'cards_lockbox2010.json', default={})
S1 = J('research', 'results', 'summary.json', default={}); S2 = J('research', 'results', 'round2', 'summary.json', default={})
L1 = J('research', 'results', 'lockbox.json', default={}); L2 = J('research', 'results', 'lockbox2.json', default={})
F = J('docs', 'desk_feed.json', default={}); D = J('data', 'daytype_score.json', default={})
e = lambda x: html.escape(str(x))
def money(x): return '$' + f'{x:,.0f}' if x is not None else '–'
def pct(x): return ('+' if x > 0 else '') + f'{x}%' if x is not None else '–'
def num(x): return '–' if x is None else f'{x:.2f}'

def spark(curve, w=560, h=150, col='var(--gold)'):
    if not curve: return ''
    ys = [v for _, v in curve]; lo, hi = min(ys + [100000]), max(ys + [100000]); hi = hi if hi > lo else lo + 1
    X = lambda i: i / (len(curve) - 1) * w; Y = lambda v: h - 6 - (v - lo) / (hi - lo) * (h - 12)
    pts = ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, (_, v) in enumerate(curve))
    base = Y(100000)
    return (f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" role="img" aria-label="Account value from $100,000">'
            f'<line x1="0" x2="{w}" y1="{base:.1f}" y2="{base:.1f}" stroke="var(--line)" stroke-dasharray="3 4"/>'
            f'<polyline fill="none" stroke="{col}" stroke-width="2" vector-effect="non-scaling-stroke" points="{pts}"/></svg>')

NAMES = dict(quantlab=('QuantLab', 'Opening candle', 'If the 9:30–9:35 candle closes above its 12 EMA, buy the Nasdaq at 9:35; below, sell. Trailing exit, re-picked monthly from 6 versions. Skips FOMC days.'),
             noiseband=('Noise band', 'Zarattini, Aziz & Barbon', 'Trade when the Nasdaq breaks outside its usual move from the open for that time of day. Checked every 30 or 60 minutes; VWAP or band stop.'),
             atrband=('ATR band', 'Open ± half a day’s range', 'Every 15 minutes from 9:45, a close above open + 0.5×ATR buys, below open − 0.5×ATR sells. Stop at the open.'),
             expiry=('Expiry reversal', 'Baltussen et al.', 'On the third Friday of each month (options expiry), sell Nasdaq and S&P futures at 9:31 and buy back at 12:00.'))

def row(label, a, b, fmt):
    return f'<tr><th>{label}</th><td>{fmt(a)}</td><td>{fmt(b)}</td></tr>'
def card_table(a, b):
    a = a or {}; b = b or {}
    return ('<table class="st"><thead><tr><th></th><th>2021–26<small>backtest</small></th><th>2011–20<small>never seen</small></th></tr></thead><tbody>'
            + row('Sharpe', a.get('sharpe'), b.get('sharpe'), num) + row('Sortino', a.get('sortino'), b.get('sortino'), num)
            + row('Result', a.get('R'), b.get('R'), lambda x: '–' if x is None else f'{x:+.1f}R')
            + row('Before costs', a.get('R_before_costs'), b.get('R_before_costs'), lambda x: '–' if x is None else f'{x:+.1f}R')
            + row('Trades', a.get('trades'), b.get('trades'), lambda x: '–' if x is None else f'{x:,}')
            + row('Win rate', a.get('win_rate'), b.get('win_rate'), lambda x: '–' if x is None else f'{x}%')
            + '</tbody></table>')

ab, bb = A.get('book', {}), B.get('book', {})
cards = ''.join(f'''<article class="card"><header><h3>{e(NAMES[k][0])}</h3><span>{e(NAMES[k][1])}</span></header><p>{e(NAMES[k][2])}</p>
{card_table(A.get('strategies', {}).get(k), B.get('strategies', {}).get(k))}</article>''' for k in NAMES)
ds = (F or {}).get('daytype_score') or D or {}
arms = ds.get('arms') or {}
dt_line = (f"{ds.get('scored_days', 0)} days scored so far" if arms else 'Scoring starts 1 January 2027')
now = dt.datetime.now(dt.timezone.utc).strftime('%d %b %Y')
risk = (P.get('config') or {}).get('risk_pct', 1.0)

page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Argon v2: can an AI trade?</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#000;--panel:#0a0a0a;--line:#232323;--ink:#ededed;--quiet:#8f8f8f;--gold:#E6B54A;--up:#3FCF8E;--down:#F25F5C;color-scheme:dark;
 box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}
@media (prefers-color-scheme:light){{:root:not([data-theme="dark"]){{--bg:#fafafa;--panel:#fff;--line:#e5e5e5;--ink:#111;--quiet:#666;--gold:#9C7320;--up:#1f8a5a;--down:#c0392b;color-scheme:light}}}}
:root[data-theme="dark"]{{--bg:#000;--panel:#0a0a0a;--line:#232323;--ink:#ededed;--quiet:#8f8f8f;--gold:#E6B54A;color-scheme:dark}}
:root[data-theme="light"]{{--bg:#fafafa;--panel:#fff;--line:#e5e5e5;--ink:#111;--quiet:#666;--gold:#9C7320;color-scheme:light}}
*{{box-sizing:border-box}}html{{scroll-padding-top:env(safe-area-inset-top,0px)}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 Geist,system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
a{{color:inherit}}main{{max-width:1080px;margin:0 auto;padding:0 clamp(18px,4vw,40px)}}
nav{{display:flex;align-items:center;gap:12px;padding:20px 0;border-bottom:1px solid var(--line);font-size:14px}}
nav b{{font-weight:600}}nav .sl{{color:var(--line)}}nav a{{color:var(--quiet);text-decoration:none}}nav a:hover{{color:var(--ink)}}nav .sp{{flex:1}}
.pill{{border:1px solid var(--line);border-radius:99px;padding:2px 10px;font:500 12px "Geist Mono",monospace;color:var(--quiet);display:inline-flex;gap:7px;align-items:center}}
.pill i{{width:6px;height:6px;border-radius:50%;background:var(--up)}}
.hero{{padding:clamp(48px,9vh,96px) 0 40px}}.hero h1{{font-size:clamp(34px,5.4vw,60px);line-height:1.05;letter-spacing:-.035em;font-weight:600;margin:14px 0 18px;max-width:14ch}}
.hero p{{font-size:clamp(17px,2vw,19px);color:var(--quiet);max-width:60ch;margin:0}}.hero p b{{color:var(--ink);font-weight:500}}
section{{padding:56px 0;border-top:1px solid var(--line)}}h2{{font-size:13px;font-weight:500;color:var(--quiet);text-transform:uppercase;letter-spacing:.08em;margin:0 0 8px;font-family:"Geist Mono",monospace}}
.lead{{font-size:clamp(22px,3vw,30px);line-height:1.25;letter-spacing:-.02em;font-weight:500;margin:0 0 24px;max-width:30ch}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line);border:1px solid var(--line);border-radius:12px;overflow:hidden}}
.era{{background:var(--panel);padding:22px}}.era h3{{margin:0;font-size:15px;font-weight:500}}.era .k{{font-size:13px;color:var(--quiet)}}
.big{{font:500 clamp(28px,4vw,40px)/1.1 "Geist Mono",monospace;letter-spacing:-.03em;margin:14px 0 2px}}.big.dn{{color:var(--down)}}
.era svg{{width:100%;height:120px;display:block;margin:12px 0}}
.kv{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;font-size:13px}}.kv span{{display:block;color:var(--quiet);font-size:12px}}.kv b{{font:500 15px "Geist Mono",monospace}}
.note{{color:var(--quiet);font-size:14px;max-width:70ch;margin:16px 0 0}}
.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}}
.card{{border:1px solid var(--line);border-radius:12px;background:var(--panel);padding:20px}}.card header{{display:flex;justify-content:space-between;align-items:baseline;gap:12px}}
.card h3{{margin:0;font-size:17px;font-weight:600}}.card header span{{color:var(--quiet);font-size:12px;font-family:"Geist Mono",monospace}}.card p{{color:var(--quiet);font-size:14px;margin:8px 0 14px}}
table.st{{width:100%;border-collapse:collapse;font-size:13px}}table.st th,table.st td{{padding:6px 0;border-top:1px solid var(--line);text-align:right;font-weight:400}}
table.st th:first-child{{text-align:left;color:var(--quiet)}}table.st td{{font-family:"Geist Mono",monospace}}table.st thead th{{border-top:0;color:var(--quiet);font-size:12px;vertical-align:bottom}}
table.st small{{display:block;font-size:11px}}
ol.steps{{list-style:none;padding:0;margin:0;display:grid;gap:1px;background:var(--line);border:1px solid var(--line);border-radius:12px;overflow:hidden}}
ol.steps li{{background:var(--panel);padding:16px 20px;display:grid;grid-template-columns:140px 1fr;gap:16px}}ol.steps b{{font:500 13px "Geist Mono",monospace;color:var(--gold)}}
ol.steps span{{color:var(--quiet);font-size:15px}}ol.steps span strong{{color:var(--ink);font-weight:500}}
.desk iframe{{width:100%;height:min(600px,78vh);border:1px solid var(--line);border-radius:12px;background:#000;display:block}}
.arms{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:16px 0 0}}.arms div{{border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:var(--panel)}}
.arms span{{display:block;color:var(--quiet);font-size:12px}}.arms b{{font:500 15px "Geist Mono",monospace}}
ul.fail{{list-style:none;padding:0;margin:0;display:grid;gap:10px}}ul.fail li{{display:grid;grid-template-columns:1fr auto;gap:4px 16px;padding:14px 0;border-top:1px solid var(--line)}}
ul.fail li b{{font-weight:500}}ul.fail li em{{font:normal 500 13px "Geist Mono",monospace;color:var(--down);white-space:nowrap}}ul.fail li span{{grid-column:1/3;color:var(--quiet);font-size:14px}}
.btn{{display:inline-block;margin-top:20px;padding:9px 16px;border:1px solid var(--line);border-radius:99px;text-decoration:none;font-size:14px}}.btn:hover{{border-color:var(--quiet)}}
section#tools .tools{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:12px;overflow:hidden}}
.tools a{{background:var(--panel);padding:18px;text-decoration:none;display:block;transition:background .15s}}.tools a:hover{{background:var(--bg)}}
.tools b{{display:block;font-weight:500;margin-bottom:4px}}.tools b::after{{content:" →";color:var(--quiet)}}.tools span{{color:var(--quiet);font-size:13px;line-height:1.45}}
@media (max-width:900px){{section#tools .tools{{grid-template-columns:repeat(2,1fr)}}}}@media (max-width:520px){{section#tools .tools{{grid-template-columns:1fr}}}}
footer{{padding:32px 0 48px;border-top:1px solid var(--line);color:var(--quiet);font-size:13px;display:flex;flex-wrap:wrap;gap:8px 20px}}footer a{{color:var(--quiet)}}
@media (max-width:760px){{.two,.grid,.arms{{grid-template-columns:1fr}}.kv{{grid-template-columns:repeat(2,1fr)}}ol.steps li{{grid-template-columns:1fr;gap:2px}}}}
</style></head><body><main>
<nav><b>Argon</b><span class="sl">/</span><span>v2</span><span class="pill"><i></i>Paper trading from 1 Jan 2027</span><span class="sp"></span><a href="#book">Book</a><a href="#method">Method</a><a href="#desk">Desk</a><a href="#failed">What failed</a><a href="#tools">Tools</a><a href="lab.html">Lab</a></nav>

<header class="hero"><span class="pill">Research project · Dru Siyani · Habs</span>
<h1>Can an AI trade?</h1>
<p>A paper-trading research desk for Nasdaq and S&amp;P futures. Every rule was <b>written down before it was tested</b>, checked against <b>ten years of data it had never seen</b>, and the failures are published next to the wins. Rules freeze on 31 December; the real test starts on 1 January.</p></header>

<section id="book"><h2>The book</h2>
<p class="lead">Four intraday momentum strategies, one account, {risk:g}% risk per trade, and any trade whose costs eat more than 10% of the risk is skipped.</p>
<div class="two">
<div class="era"><h3>2021–2026</h3><span class="k">The backtest. Mostly in-sample: the settings were chosen on it.</span>
<div class="big">{money(ab.get('final'))}</div><span class="k">from $100,000</span>{spark(ab.get('curve'))}
<div class="kv"><div><span>Sharpe</span><b>{num(ab.get('sharpe'))}</b></div><div><span>Sortino</span><b>{num(ab.get('sortino'))}</b></div><div><span>Worst drop</span><b>{ab.get('worst_drop','–')}%</b></div><div><span>Trades</span><b>{ab.get('trades','–'):,}</b></div></div></div>
<div class="era"><h3>2011–2020</h3><span class="k">Never seen while building it. Opened once, 28 Oct 2026.</span>
<div class="big dn">{money(bb.get('final'))}</div><span class="k">from $100,000</span>{spark(bb.get('curve'), col='var(--down)')}
<div class="kv"><div><span>Sharpe</span><b>{num(bb.get('sharpe'))}</b></div><div><span>Sortino</span><b>{num(bb.get('sortino'))}</b></div><div><span>Worst drop</span><b>{bb.get('worst_drop','–')}%</b></div><div><span>Trades</span><b>{bb.get('trades','–'):,}</b></div></div></div>
</div>
<p class="note">The honest reading: these edges only show up in the more volatile markets since 2018. In the calm years of 2011–2017 the book lost money. Research on intraday momentum finds the same thing: it works when volatility is high and options dealers are short gamma, and fades when markets are calm. So Argon v2 is a bet that today’s market regime continues. Live results will likely be well below the backtest.</p>
<div class="grid" style="margin-top:24px">{cards}</div></section>

<section id="method"><h2>Method</h2>
<p class="lead">How each claim was earned.</p>
<ol class="steps">
<li><b>Pre-registered</b><span>Pass marks, test windows and every adjustment were committed to GitHub <strong>before</strong> any test ran. The commit timestamps are the proof.</span></li>
<li><b>Real costs</b><span>Round-trip costs on every trade, extra stop slippage in the first 15 minutes, limit orders that only fill if price trades through, roll days and FOMC afternoons skipped, then everything re-run at <strong>double costs</strong>.</span></li>
<li><b>Walk-forward</b><span>Strategies that re-pick settings only ever use months that have already happened.</span></li>
<li><b>Round 1</b><span><strong>{S1.get('tested', 109)} adjustments</strong> tested; {len(S1.get('survivors', ['Q24']))} survived and passed its lockbox (QuantLab skipping FOMC days).</span></li>
<li><b>Round 2</b><span><strong>{S2.get('tested', 17)} adjustments</strong> after a council review; {len(S2.get('survivors', []))} survived (risk parity). Then the base book was tested on 2011–2020 and <strong>failed</strong>.</span></li>
<li><b>Bugs found</b><span>A daily loss limit that looked good only because of lookahead; roll days that were never actually skipped; a missing 2010–2020 FOMC calendar; September 2026 counted twice. All fixed and published.</span></li>
<li><b>Freeze</b><span>From 31 Dec 23:59 UTC nothing changes except an emergency kill switch. Every change before then is logged in <a href="https://github.com/drusiyani/argon-v2/blob/main/PREREGISTRATION.md">PREREGISTRATION.md</a>.</span></li>
</ol></section>

<section id="desk" class="desk"><h2>The AI desk</h2>
<p class="lead">Every morning before the open, an AI forecasts whether today will be a trend day or a chop day, and picks a size for the book.</p>
<p class="note" style="margin:0 0 18px">It runs in the shadow next to two other arms: the plain book at 1×, and a one-line rule (size by yesterday’s range). The AI only gets real control after 120 trading days, and only if it beats <strong>both</strong> by 0.15 Sharpe. Same model, frozen prompt, middle answer of three runs. {e(dt_line)}.</p>
<iframe src="desk.html" loading="lazy" title="The Argon desk: agents in their rooms passing real messages"></iframe>
<div class="arms">{''.join(f'<div><span>{e(k)}</span><b>{num(v.get("sharpe")) if v.get("sharpe") is not None else "starts 1 Jan"}</b></div>' for k, v in (arms or {'1×': {}, 'Dumb rule': {}, 'AI': {}}).items())}</div>
<a class="btn" href="desk.html">Open the desk full screen →</a></section>

<section id="failed"><h2>What failed</h2>
<p class="lead">Most ideas didn’t survive. Here are the big ones.</p>
<ul class="fail">
<li><b>The original “liquidity sweep” strategy (ICT)</b><em>+40.8R → −16.3R</em><span>Sweep of a level, structure shift, fair value gap. Profitable until realistic costs and slippage were added. Still runs in the old dashboard as a separate AI experiment.</span></li>
<li><b>15+ influencer strategies</b><em>all lost</em><span>CRT, “sweeping inverse” FVGs, a $328k ICT model, dip-buying RSI. Lesson: following the push works on the Nasdaq; fading it loses after costs.</span></li>
<li><b>A daily loss limit</b><em>lookahead bug</em><span>Looked like +0.09 Sharpe; with exact trade times it made results worse.</span></li>
<li><b>The v2 book on 2011–2020</b><em>Sharpe −1.03</em><span>Ten never-seen years, opened once. Across all their trades, three of four strategies had a small edge before costs and QuantLab had none. Adding the cost rule afterwards lifted it to {num(bb.get('sharpe'))}, still a loss ({money(bb.get('final'))} from $100,000), and that fix was chosen after seeing the result. Published anyway.</span></li>
</ul>
<a class="btn" href="lab.html">Open the full dashboard →</a></section>

<section id="tools"><h2>Everything else</h2>
<p class="lead">All of Argon’s tools are still here.</p>
<div class="tools">
<a href="lab.html#overview"><b>Full dashboard</b><span>Every number, every strategy, the live farm and the original desk experiment.</span></a>
<a href="lab.html#chart"><b>Charts</b><span>Live futures charts with Argon’s levels, setups and trades drawn on.</span></a>
<a href="lab.html#lab"><b>Strategy lab</b><span>The rule variants Argon tests, how each one scores, and the monthly re-pick.</span></a>
<a href="lab.html#studies"><b>Studies</b><span>The research write-ups: influencer strategies, papers, and what each one taught.</span></a>
<a href="lab.html#events"><b>Events</b><span>The farm’s event log: sweeps, structure breaks and fills as they happen.</span></a>
<a href="https://github.com/drusiyani/argon-v2/tree/main/vault"><b>The brain (Obsidian)</b><span>Argon’s notes: rulebooks, lessons, levels, markets and reviews, linked like a second brain.</span></a>
<a href="desk.html"><b>The 3D desk</b><span>The agents in their rooms, passing the desk’s real messages.</span></a>
<a href="https://github.com/drusiyani/argon-v2/tree/main/research"><b>Research code</b><span>Every test script and result, so anyone can re-run them.</span></a>
</div></section>
<footer><span>Argon v2 · built by Dru Siyani · updated {now}</span><a href="https://github.com/drusiyani/argon-v2">GitHub</a><a href="https://github.com/drusiyani/argon-v2/blob/main/PREREGISTRATION.md">Pre-registration</a><a href="https://github.com/drusiyani/argon-v2/tree/main/research/results">Research results</a><span>Paper trading only. Not financial advice.</span></footer>
</main></body></html>'''
open(os.path.join(ROOT, 'docs', 'index.html'), 'w').write(page); print('built docs/index.html (front page)', len(page))
