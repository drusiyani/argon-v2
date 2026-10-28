<script>
"use strict";
// Portfolio v2 panel (Amendment 3). Data: data/portfolio.json, injected by build_site.py as window.PORT.
(function(){const P=window.PORT,el=document.getElementById('portv2');if(!P||!el)return;
const f=n=>'$'+Math.round(n).toLocaleString('en-US'),pc=n=>(n>0?'+':'')+n+'%',M=P.main,S=P.shadow;
const css=`#portv2{margin:28px 0;border:1px solid var(--line);border-radius:12px;background:var(--panel);padding:20px 22px}
#portv2 h2{margin:0 0 4px;font-size:18px;font-weight:600}#portv2 .sub{color:var(--muted);font-size:13px;margin:0 0 16px}
#portv2 .k{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:8px;overflow:hidden;margin-bottom:16px}
#portv2 .k div{background:var(--panel);padding:10px 12px}#portv2 .k span{display:block;color:var(--faint);font-size:11px;letter-spacing:.06em;text-transform:uppercase}#portv2 .k b{font-size:18px;font-weight:600}
#portv2 svg{width:100%;height:150px;display:block}#portv2 table{width:100%;border-collapse:collapse;font-size:13px;margin-top:12px}
#portv2 td,#portv2 th{padding:6px 8px;border-top:1px solid var(--line2);text-align:right}#portv2 th{color:var(--faint);font-weight:500}#portv2 td:first-child,#portv2 th:first-child{text-align:left}
#portv2 .up{color:var(--up)}#portv2 .dn{color:var(--down)}#portv2 .note{color:var(--muted);font-size:12px;margin:12px 0 0;line-height:1.5}
#portv2 .st{display:inline-block;font-size:12px;padding:2px 8px;border-radius:99px;border:1px solid var(--line);margin-left:8px;vertical-align:2px}#portv2 .st.kill{color:var(--down);border-color:var(--down)}
#portv2 .desk{margin-top:18px}#portv2 .desk iframe{width:100%;height:min(560px,75vh);border:1px solid var(--line);border-radius:10px;background:#000;display:block}#portv2 .desk a{display:inline-block;margin-top:8px;font-size:13px;color:var(--gold);text-decoration:none}#portv2 .lg{display:flex;gap:16px;font-size:12px;color:var(--muted);margin-top:6px}#portv2 .lg i{display:inline-block;width:14px;height:2px;vertical-align:3px;margin-right:6px}`;
const pts=(arr,w,h,lo,hi)=>arr.map((p,i)=>`${(i/(arr.length-1)*w).toFixed(1)},${(h-(Math.log(p[1])-lo)/(hi-lo)*h).toFixed(1)}`).join(' ');
const all=[...M.equity,...S.equity].map(p=>Math.log(p[1])),lo=Math.min(...all),hi=Math.max(...all);
const yrs=Object.keys(M.years).map(y=>`<tr><td>${y}${y==='2021'?' (Jul-Dec)':''}</td><td class="${M.years[y].usd>=0?'up':'dn'}">${M.years[y].usd>=0?'+':'−'}${f(Math.abs(M.years[y].usd))}</td><td class="${M.years[y].pct>=0?'up':'dn'}">${pc(M.years[y].pct)}</td><td>${S.years[y]?pc(S.years[y].pct):''}</td></tr>`).join('');
el.innerHTML=`<style>${css}</style><h2>Portfolio v2<span class="st ${P.killed?'kill':''}">${P.killed?'Stopped by kill switch':'Ready for 1 Jan 2027'}</span></h2>
<p class="sub">QuantLab (skips FOMC days), noise band, ATR band and the expiry reversal, skipping any trade whose cost is over 10% of 1R. ${P.config.risk_pct}% risk per trade, no daily loss limit. Backtest ${P.window[0]} to ${P.window[1]}, real costs, $100k start.</p>
<div class="k"><div><span>$100k became</span><b>${f(M.final)}</b></div><div><span>A year</span><b>${pc(M.a_year)}</b></div><div><span>Sharpe</span><b>${M.sharpe}</b></div><div><span>Worst drop</span><b class="dn">${M.worst_drop}%</b></div><div><span>Double costs</span><b>${f(P.double_costs.final)}</b></div></div>
<svg viewBox="0 0 600 150" preserveAspectRatio="none" aria-label="Account value, log scale"><polyline fill="none" stroke="var(--faint)" stroke-width="1.2" stroke-dasharray="3 3" points="${pts(S.equity,600,146,lo,hi)}"/><polyline fill="none" stroke="var(--gold)" stroke-width="2" points="${pts(M.equity,600,146,lo,hi)}"/></svg>
<div class="lg"><span><i style="background:var(--gold)"></i>Main book</span><span><i style="background:var(--faint)"></i>Shadow: ${P.config.shadow.name}, Sharpe ${S.sharpe}</span></div>
<table><tr><th>Year</th><th>Profit</th><th>Return</th><th>Shadow</th></tr>${yrs}</table>
<div class="desk"><iframe src="desk.html" loading="lazy" title="The Argon desk: bots in their rooms passing messages"></iframe><a href="desk.html">Open the desk full screen →</a></div><p class="note">${P.honesty.join(' ')} The shadow is pre-registered and judged on ${P.config.shadow.judged_on}; it never changes the main book.</p>`})();
</script>
