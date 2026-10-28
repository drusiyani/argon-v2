<script>
"use strict";
const RISK=1;   // % of the account risked per trade (1R). Change it here only; the text below says 1% to match.
const D=JSON.parse(document.getElementById('data').textContent);
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const RB='Rulebook v'+D.rules;
const INSTS=D.insts, KINDS=D.kinds, NAMES=D.names, DAYS=D.days;
const INAME={NQ:'Nasdaq-100 e-mini',ES:'S&P 500 e-mini',YM:'Dow e-mini',RTY:'Russell 2000 e-mini'};
const TFN=['5m','15m','1h','session'];
const fmtR=x=>x==null?'–':(x>0?'+':'')+x.toFixed(2)+'R';
const cls=x=>x>0?'pos':x<0?'neg':'dim';
const px=(v,i)=>v==null?'–':(i==='YM'?v.toLocaleString('en-US',{maximumFractionDigits:0}):i==='RTY'?v.toFixed(1):v.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}));
// NY time helpers (cached per hour)
const NYF=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',hourCycle:'h23',weekday:'short'});
const hc=new Map();
function nyH(sec){const k=Math.floor(sec/3600);let v=hc.get(k);if(!v){const p={};NYF.formatToParts(new Date(k*3600000)).forEach(x=>p[x.type]=x.value);v={y:+p.year,mo:+p.month,d:+p.day,h:+p.hour,wd:p.weekday};hc.set(k,v)}return v}
const nyMin=sec=>{const v=nyH(sec);return v.h*60+Math.floor(sec/60)%60};
const hhmm=sec=>{const m=nyMin(sec);return String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0')};
const dlab=sd=>{const d=new Date(sd+'T12:00:00Z');return d.toLocaleDateString('en-GB',{weekday:'short',day:'numeric',month:'short'})};
const DOW=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
// ---------- bars
function decodeBars(pb){const n=pb.t.length,tk=pb.tick,t=new Float64Array(n),o=new Float64Array(n),h=new Float64Array(n),l=new Float64Array(n),c=new Float64Array(n),v=new Float64Array(n),sd=new Array(n);
  let tt=0,pc=0,j=0;for(const [d,cnt] of pb.sd)for(let k=0;k<cnt;k++)sd[j++]=d;
  for(let i=0;i<n;i++){tt+=pb.t[i];t[i]=tt*60;const oo=pc+pb.o[i];o[i]=oo*tk;h[i]=(oo+pb.h[i])*tk;l[i]=(oo-pb.l[i])*tk;const cc=oo+pb.c[i];c[i]=cc*tk;pc=cc;v[i]=pb.v[i]}
  return {n,t,o,h,l,c,v,sd}}
function resample(B,mins){const P=mins*60,out={t:[],o:[],h:[],l:[],c:[],v:[],sd:[]};let key=null;
  for(let i=0;i<B.n;i++){const k=B.sd[i]+'|'+Math.floor(B.t[i]/P);if(k!==key){key=k;out.t.push(Math.floor(B.t[i]/P)*P);out.o.push(B.o[i]);out.h.push(B.h[i]);out.l.push(B.l[i]);out.c.push(B.c[i]);out.v.push(B.v[i]);out.sd.push(B.sd[i])}
  else{const j=out.t.length-1;if(B.h[i]>out.h[j])out.h[j]=B.h[i];if(B.l[i]<out.l[j])out.l[j]=B.l[i];out.c[j]=B.c[i];out.v[j]+=B.v[i]}}out.n=out.t.length;return out}
const BARS={};
for(const s of Object.keys(D.chart)){BARS[s]={};BARS[s]['5m']=decodeBars(D.chart[s]['5m']);if(D.chart[s]['2m'])BARS[s]['2m']=decodeBars(D.chart[s]['2m']);}
function bars(s,tf){if(!BARS[s][tf]){BARS[s][tf]=resample(BARS[s]['5m'],tf==='15m'?15:60)}return BARS[s][tf]}
function bsearch(arr,x){let lo=0,hi=arr.length-1,r=-1;while(lo<=hi){const m=(lo+hi)>>1;if(arr[m]<=x){r=m;lo=m+1}else hi=m-1}return r}
// ---------- events
const E=(()=>{const P=D.events,n=P.t.length,t=new Float64Array(n),inst=new Uint8Array(n),tf=new Uint8Array(n),k=new Uint8Array(n),p=new Float64Array(n),sd=new Array(n);let tt=0;
  for(let i=0;i<n;i++){tt+=P.t[i];t[i]=tt*60;inst[i]=P.i[i];tf[i]=P.f[i];k[i]=P.k[i];const s=INSTS[P.i[i]];p[i]=P.p[i]==null?NaN:P.p[i]*D.tick[s]}
  return {n,t,inst,tf,k,p,x:P.x,sd}})();
// session date per event via 5m bars
for(let i=0;i<E.n;i++){const B=BARS[INSTS[E.inst[i]]]['5m'];let j=bsearch(B.t,E.t[i]);if(j<0)j=0;E.sd[i]=B.sd[j]}
const KI={};KINDS.forEach((k,i)=>KI[k]=i);
const FN={pool_formed:'Key level marked',sweep:'Level swept',manip_leg:'Big push candle',smt:'Markets disagree (SMT)',swing:'Swing high or low',structure_break:'Trend break',mss_failed:'Failed trend break',inducement:'Bait level',fvg_formed:'Price gap (FVG)',fvg_inverted:'Gap failed',ob_formed:'Order block',ob_mitigated:'Order block retested',ob_invalidated:'Order block broken',session_open:'Session opens',fire:'Trade taken',ob_entry:'Order-block trade taken',refusal:'Trade skipped',outcome:'Trade result'};
const IDX=new Map();// sd|inst -> event idx list
for(let i=0;i<E.n;i++){const key=E.sd[i]+'|'+INSTS[E.inst[i]];let a=IDX.get(key);if(!a){a=[];IDX.set(key,a)}a.push(i)}
const tickOf=s=>D.tick[s];
const LABS=['HH','HL','LH','LL'],CLSN=['manipulation','delayed','acceptance'],WINN=[null,'London','NY'],BT=['BOS','CHoCH','MSS'],PKN=['session','swing','eq'];
function evObj(i){const s=INSTS[E.inst[i]],k=KINDS[E.k[i]],x=E.x[i],tk=tickOf(s),o={id:i,kind:k,inst:s,tf:TFN[E.tf[i]],t:E.t[i],time:hhmm(E.t[i])+' NY',day:E.sd[i],price:isNaN(E.p[i])?null:E.p[i]};
  const T=m=>m?m*60:null;
  switch(k){
  case 'swing':o.label=LABS[x];break;
  case 'pool_formed':Object.assign(o,{name:NAMES[x[0]],side:x[1]?'buy-side (above)':'sell-side (below)',pool_kind:PKN[x[2]],ends:T(x[3]),swept:!!x[4],touches:x[5]});break;
  case 'sweep':Object.assign(o,{pool:NAMES[x[0]],side:x[1]?'high':'low',pool_kind:PKN[x[2]],class:CLSN[x[3]],window:WINN[x[4]],extreme:x[5]*tk,smt:!!x[6]});break;
  case 'manip_leg':Object.assign(o,{level:x[0]*tk,side:x[1]?'high':'low'});break;
  case 'smt':Object.assign(o,{pool:NAMES[x[0]],side:x[1]?'high':'low',pair:INSTS[x[2]],pair_level:x[3]*tickOf(INSTS[x[2]])});break;
  case 'structure_break':Object.assign(o,{type:BT[x[0]],direction:x[1]>0?'up':'down',displacement:!!x[2],from:T(x[3])});break;
  case 'mss_failed':Object.assign(o,{direction:x[0]>0?'up':'down',type:BT[x[1]]});break;
  case 'inducement':Object.assign(o,{direction:x[0]>0?'up':'down',taken:T(x[1]),ends:T(x[2])});break;
  case 'fvg_formed':case 'ob_formed':Object.assign(o,{bottom:x[0]*tk,top:o.price,direction:x[1]>0?'bullish':'bearish',ends:T(x[2]),mitigated:T(x[3]),inverted:T(x[4])});break;
  case 'fvg_inverted':case 'ob_mitigated':case 'ob_invalidated':Object.assign(o,{bottom:x[0]*tk,top:o.price,direction:x[1]>0?'bullish':'bearish'});break;
  case 'session_open':o.name=NAMES[x];break;
  case 'fire':case 'ob_entry':o.trade=D.trades[x[0]].id;o.tradeIdx=x[0];break;
  case 'refusal':o.trade=D.trades[x[0]].id;o.tradeIdx=x[0];o.step=x[1];break;
  case 'outcome':o.trade=D.trades[x[0]].id;o.tradeIdx=x[0];o.R=x[1];break}
  return o}
function evText(o){switch(o.kind){
  case 'swing':return `${{HH:'higher high',HL:'higher low',LH:'lower high',LL:'lower low'}[o.label]} at ${px(o.price,o.inst)}`;
  case 'pool_formed':return `${o.name} at ${px(o.price,o.inst)}, ${o.side.startsWith('buy')?'stops likely sit above it':'stops likely sit below it'}${o.touches>1?`, touched ${o.touches} times`:''}${o.swept?'':' (never taken)'}`;
  case 'sweep':return `price poked past ${o.pool} ${px(o.price,o.inst)} to ${px(o.extreme,o.inst)} and ${o.class==='acceptance'?'stayed there (a breakout)':o.class==='delayed'?'came back within 10 min':'came straight back'}${o.window?`, ${o.window} session`:''}${o.smt?', and the other market didn\'t follow':''}`;
  case 'manip_leg':return `one unusually big candle pushed through ${px(o.level,o.inst)}`;
  case 'smt':return `${o.inst} went past its ${o.pool} but ${o.pair} didn't go past its own (${px(o.pair_level,o.pair)}): a warning the move is fake`;
  case 'structure_break':return `${o.type==='BOS'?'trend continued':o.type==='MSS'?'trend flipped, with a big candle':'trend flipped'} ${o.direction==='up'?'upwards':'downwards'} through ${px(o.price,o.inst)}`;
  case 'mss_failed':return `a trend flip ${o.direction==='up'?'upwards':'downwards'} that reversed within 15 min`;
  case 'inducement':return `obvious ${o.direction==='up'?'low':'high'} at ${px(o.price,o.inst)} that traders put stops behind${o.taken?', taken at '+hhmm(o.taken):', never taken'}`;
  case 'fvg_formed':return `price moved so fast it left a gap from ${px(o.bottom,o.inst)} to ${px(o.top,o.inst)}${o.inverted?', later failed at '+hhmm(o.inverted):''}`;
  case 'fvg_inverted':return `price closed right through the gap, so it no longer counts`;
  case 'ob_formed':return `last ${o.direction==='bullish'?'down':'up'} candle before a big move, ${px(o.bottom,o.inst)} to ${px(o.top,o.inst)}: a zone price often returns to`;
  case 'ob_mitigated':return `price came back to the order block`;
  case 'ob_invalidated':return `price closed through the order block, so it no longer counts`;
  case 'session_open':return `${o.name} at ${px(o.price,o.inst)}`;
  case 'fire':{const t=TR[o.tradeIdx];return `main strategy ${t.side==='short'?'sold':'bought'} at ${px(t.entry,t.inst)}, grade ${t.grade}`}
  case 'ob_entry':{const t=TR[o.tradeIdx];return `order-block strategy ${t.side==='short'?'sold':'bought'} at ${px(t.entry,t.inst)}`}
  case 'refusal':{const t=TR[o.tradeIdx];const w=t.steps[o.step]?t.steps[o.step][1]:'already in a trade on this market';return `skipped (${(STEPL[o.step]||'one trade at a time').toLowerCase()}): ${w}`}
  case 'outcome':{const t=TR[o.tradeIdx];return `${t.route==='ob'?'order-block':'main'} trade ${t.status==='win'?'hit its target':t.status==='loss'?'hit its stop':'closed at the end of the day'}: ${fmtR(o.R)}`}}return ''}
// ---------- trades
const TR=D.trades;TR.forEach((t,i)=>{t.idx=i;for(const k of['sweep_t','mss_t','fill_t','exit_t'])if(t[k])t[k]*=60;t.walked=t.R!=null;
  t.family=t.route==='ob'?'15m order block':(t.pool_kind==='session'?({PDH:"yesterday's high or low",PDL:"yesterday's high or low",PWH:"last week's high or low",PWL:"last week's high or low"}[t.pool]||t.pool.split(' ')[0]+' high or low'):t.pool_kind==='eq'?'equal highs and lows':t.pool_tf+' high or low')});
const ORBT=TR.filter(t=>t.route==='orb'&&t.fired);
const FEED=TR.filter(t=>t.route==='feed'),BUSY=TR.filter(t=>t.route==='busy'&&t.fired);
const FIRED=TR.filter(t=>t.route==='chain'&&t.fired),OBB=TR.filter(t=>t.route==='ob'&&t.fired),SHADOW=TR.filter(t=>t.route==='chain'&&!t.fired&&t.walked);
const sumR=a=>a.reduce((s,t)=>s+(t.R||0),0);
function stats(a){const w=a.filter(t=>t.R>0).length,n=a.length,g=sumR(a);return{n,w,wr:n?w/n:0,g,net:g-0.05*n,avg:n?g/n:0,best:n?Math.max(...a.map(t=>t.R)):0,worst:n?Math.min(...a.map(t=>t.R)):0}}
function scoreParts(t){if(t.route==='ob')return null;const pq=t.pool_kind==='session'?25:t.pool_kind==='eq'?20:({'1h':22,'15m':15,'5m':5}[t.pool_tf]||5);
  return [['pool quality',pq,25],['SMT',t.smt?15:0,15],['displacement',t.disp||0,20],['1h bias',t.bias?15:0,15],['premium/discount',t.pd?10:0,10],['window',t.win==='NY'?10:6,10],['FVG+OB overlap',t.overlap?5:0,5]]}
// theme + tabs
const root=document.documentElement;
function setTheme(th){root.setAttribute('data-theme',th);$('#themeBtn').textContent=th==='dark'?'Light':'Dark';try{localStorage.setItem('argon2-theme',th)}catch(e){}}
let th0=null;try{th0=localStorage.getItem('argon2-theme')}catch(e){}setTheme(th0||'dark');
function setViewMode(m){root.setAttribute('data-mode',m);$('#modeBtn').textContent=m==='simple'?'Advanced':'Simple';try{localStorage.setItem('argon2-mode',m)}catch(e){}
  if(typeof renderInspector==='function'&&C&&C.sel)renderInspector();if(!$('#chart').hidden){if(m==='simple'&&C.view2!=='tv'){const b=document.querySelector('#cView [data-v="tv"]');if(b&&window.LightweightCharts)b.click()}else draw()}if(m==='simple'&&!$('#events').hidden)openTab('overview')}
let md0=null;try{md0=localStorage.getItem('argon2-mode')}catch(e){}
$('#modeBtn').onclick=()=>setViewMode(root.getAttribute('data-mode')==='simple'?'advanced':'simple');
$('#themeBtn').onclick=()=>{setTheme(root.getAttribute('data-theme')==='dark'?'light':'dark');if(!$('#chart').hidden)draw();if(!$('#studies').hidden&&GRAPH.on)drawGraph()};
$('#ver').textContent=`argon ${D.rules}·${D.sig}`;
function openTab(id){$$('nav button').forEach(b=>b.setAttribute('aria-selected',b.dataset.tab===id));$$('main>section').forEach(s=>s.hidden=s.id!==id);
  if(id==='chart')requestAnimationFrame(()=>{resize();if(root.getAttribute('data-mode')==='simple'&&!C.view2&&window.LightweightCharts){const b=document.querySelector('#cView [data-v="tv"]');if(b){b.click();return}}draw()});if(id==='events')renderEvents();if(id==='studies'&&!NOTE)openNote(DAYS.at(-1));if(id==='lab')renderLab()}
$$('nav button').forEach(b=>b.onclick=()=>openTab(b.dataset.tab));
const css=v=>getComputedStyle(root).getPropertyValue(v).trim();
