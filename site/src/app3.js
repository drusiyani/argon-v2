// ================= CHART
const C={inst:'NQ',day:DAYS.at(-1),tf:'5m',mode:'declutter',view:null,sel:null,hover:-1,tfvis:{'5m':'bright','15m':'bright','1h':'bright'}};
const LAYERS=[
 ['pools','key levels (highs and lows)','--blue',1,1],['levels','yesterday, last week, Asia and London levels','--gold2',1,1],['sweeps','levels swept','--gold',1,1],['manip','big push candles','--red',0,1],
 ['smt','markets disagree (SMT)','--cyan',1,1],['idm','bait levels','--muted',0,1],['trades','★★ trades taken','--up',1,1],['seen','○ trades skipped','--up',1,1],
 ['obbook','order-block trades','--violet',1,1],['swings','highs and lows (HH, HL, LH, LL)','--grey',0,1],['breaks','trend breaks','--ink',1,1],['mssf','failed trend breaks','--red',0,1],
 ['ob','order blocks','--violet',1,1],['fvg','price gaps (FVG)','--purple',0,1],['sess','session opens','--grey',1,1]];
const LON={};LAYERS.forEach(l=>LON[l[0]]=l[3]===1);
function setMode(m){C.mode=m;LAYERS.forEach(l=>LON[l[0]]=m==='everything'?true:l[3]===1);$('#mDeclutter').setAttribute('aria-pressed',m==='declutter');$('#mEverything').setAttribute('aria-pressed',m==='everything');renderLayers();draw()}
$('#mDeclutter').onclick=()=>setMode('declutter');$('#mEverything').onclick=()=>setMode('everything');
// controls
$('#cInst').innerHTML=D.insts.map(s=>`<option>${s}</option>`).join('');
$('#cDay').innerHTML=DAYS.slice().reverse().map(d=>`<option value="${d}">${d} ${DOW[new Date(d+'T12:00:00Z').getUTCDay()===0?6:new Date(d+'T12:00:00Z').getUTCDay()-1]}</option>`).join('');
$('#cInst').onchange=e=>{C.inst=e.target.value;C.view=null;C.sel=null;draw();renderLayers()};
$('#cDay').onchange=e=>setDay(e.target.value);
$('#cPrev').onclick=()=>stepDay(-1);$('#cNext').onclick=()=>stepDay(1);
function stepDay(d){const i=DAYS.indexOf(C.day)+d;if(i>=0&&i<DAYS.length)setDay(DAYS[i])}
function setDay(d){C.day=d;$('#cDay').value=d;C.view=null;C.sel=null;renderTF();renderLayers();draw()}
function renderTF(){const has2=!!BARS[C.inst]['2m']&&C.day>=D.two_min_from;if(C.tf==='2m'&&!has2)C.tf='5m';
  $('#cTF').innerHTML=['2m','5m','15m','1h'].map(t=>`<button type="button" class="chip" data-tf="${t}" aria-pressed="${C.tf===t}" ${t==='2m'&&!has2?'disabled title="2m tape starts '+D.two_min_from+'"':''}>${t}</button>`).join('');
  $$('#cTF .chip').forEach(b=>b.onclick=()=>{C.tf=b.dataset.tf;C.view=null;renderTF();draw()})}
const isTouch=matchMedia('(pointer:coarse)').matches;
$('#cHint').textContent=isTouch?'pinch to zoom · drag to move · tap anything to explain it':'scroll to zoom · drag to move · ←/→ change day · 0 resets · click anything to explain it';
function gotoChart(s,d,t,selObj){C.inst=s;$('#cInst').value=s;openTab('chart');setDay(d);if(t){const B=dayBars();const j=bsearch(B.t,t);if(j>=0){const w=Math.min(B.n,120);C.view={i0:Math.max(0,j-w/2),i1:Math.min(B.n,j+w/2)}}}if(selObj){C.sel=selObj;renderInspector()}draw()}
let DB=null;
function dayBars(){const B=bars(C.inst,C.tf);if(DB&&DB.key===C.inst+C.tf+C.day)return DB;let a=-1,b=-1;for(let i=0;i<B.n;i++){if(B.sd[i]===C.day){if(a<0)a=i;b=i}else if(a>=0)break}
  const n=a<0?0:b-a+1;DB={key:C.inst+C.tf+C.day,n,t:Array.from(B.t.slice(a,a+n)),o:B.o.slice(a,a+n),h:B.h.slice(a,a+n),l:B.l.slice(a,a+n),c:B.c.slice(a,a+n),v:B.v.slice(a,a+n)};return DB}
function dayEvents(back=0){const out=[];const di=DAYS.indexOf(C.day);for(let k=Math.max(0,di-back);k<=di;k++){const a=IDX.get(DAYS[k]+'|'+C.inst);if(a)out.push(...a)}return out}
// canvas
const cv=$('#cv');let G=null,W=0,H=0,HITS=[];
function resize(){const r=cv.getBoundingClientRect(),dpr=devicePixelRatio||1;W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;G=cv.getContext('2d');G.setTransform(dpr,0,0,dpr,0,0)}
addEventListener('resize',()=>{if(!$('#chart').hidden){resize();draw()}});
const visTF=tf=>tf==='session'||!C.tfvis[tf]||C.tfvis[tf]!=='hidden';
const alphaTF=tf=>C.tfvis[tf]==='ghost'?.35:1;
function draw(){if($('#chart').hidden)return;if(typeof tvLinkUpdate==='function')tvLinkUpdate();if(C.view2==='tv'){if(typeof drawTV==='function')drawTV();renderStats(dayBars());return}if(!G)resize();const B=dayBars();G.clearRect(0,0,W,H);HITS=[];
  renderStats(B);if(!B.n){G.fillStyle=css('--muted');G.font='13px '+css('--mono');G.fillText('No tape for this session.',20,30);return}
  if(!C.view)C.view={i0:0,i1:B.n};const v=C.view;v.i0=Math.max(-5,Math.min(v.i0,B.n-5));v.i1=Math.max(v.i0+5,Math.min(v.i1,B.n+20));
  const R=70,T=12,Bt=24,pw=W-R,ph=H-T-Bt,bw=pw/(v.i1-v.i0);
  let hi=-Infinity,lo=Infinity;for(let i=Math.max(0,Math.floor(v.i0));i<Math.min(B.n,Math.ceil(v.i1));i++){if(B.h[i]>hi)hi=B.h[i];if(B.l[i]<lo)lo=B.l[i]}
  if(!isFinite(hi)){hi=B.h[0];lo=B.l[0]}const pad=(hi-lo)*.07||1;hi+=pad;lo-=pad;
  const X=j=>(j-v.i0+.5)*bw,Y=p=>T+(hi-p)*ph/(hi-lo);
  const xt=t=>{if(t<B.t[0])return X(-.5)-2;const j=bsearch(B.t,t);return X(j)};
  const xtEnd=t=>{if(t==null)return X(B.n);if(t>B.t[B.n-1]+3600)return X(B.n);return xt(t)};
  const inY=p=>p>=lo&&p<=hi;
  const ctx=G;const col=v_=>css(v_);
  // windows
  let s0=-1;const shade=(a,b,c)=>{let st=-1,en=-1;for(let i=0;i<B.n;i++){const m=nyMin(B.t[i]);if(m>=a&&m<b){if(st<0)st=i;en=i}}if(st>=0){ctx.fillStyle=c;ctx.fillRect(X(st)-bw/2,T,(en-st+1)*bw,ph)}};
  shade(120,300,'rgba(91,141,239,.05)');shade(510,690,'rgba(230,181,74,.06)');
  // grid + price axis
  ctx.font='10.5px '+css('--mono');ctx.textAlign='left';
  for(let k=0;k<=6;k++){const p=lo+(hi-lo)*k/6,y=Y(p);ctx.strokeStyle=col('--line2');ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(pw,y);ctx.stroke();ctx.fillStyle=col('--faint');ctx.fillText(px(p,C.inst),pw+6,y+3)}
  // time axis
  let lastLab=-1e9;for(let i=Math.max(0,Math.ceil(v.i0));i<Math.min(B.n,v.i1);i++){const m=nyMin(B.t[i]);const step=bw*12>60?60:bw*12>30?120:240;if(m%step===0&&X(i)-lastLab>46){lastLab=X(i);ctx.fillStyle=col('--faint');ctx.fillText(String(Math.floor(m/60)).padStart(2,'0')+':00',X(i)-14,H-8);ctx.strokeStyle=col('--line2');ctx.beginPath();ctx.moveTo(X(i),T);ctx.lineTo(X(i),T+ph);ctx.stroke()}}
  ctx.save();ctx.beginPath();ctx.rect(0,0,pw,H-Bt+4);ctx.clip();
  const evs=dayEvents(0),evsBack=dayEvents(8);
  const hit=(pri,x0,y0,x1,y1,type,ref)=>HITS.push({pri,x0:Math.min(x0,x1),y0:Math.min(y0,y1),x1:Math.max(x0,x1),y1:Math.max(y0,y1),type,ref});
  // session opens
  if(LON.sess)for(const i of evs){if(E.k[i]!==KI.session_open)continue;const x=xt(E.t[i]);ctx.strokeStyle=col('--grey');ctx.setLineDash([2,4]);ctx.globalAlpha=.6;ctx.beginPath();ctx.moveTo(x,T);ctx.lineTo(x,T+ph);ctx.stroke();ctx.setLineDash([]);ctx.globalAlpha=1;ctx.fillStyle=col('--faint');ctx.fillText(NAMES[E.x[i]].replace(' open',''),x+3,T+10);hit(1,x-3,T,x+3,T+ph,'event',i)}
  // zones
  const dayStart=B.t[0],dayEnd=B.t[B.n-1]+300;
  for(const i of dayEvents(1)){const k=E.k[i];if(k!==KI.ob_formed&&k!==KI.fvg_formed)continue;const isOB=k===KI.ob_formed;if(isOB?!LON.ob:!LON.fvg)continue;const tf=TFN[E.tf[i]];if(!visTF(tf))continue;
    if(C.mode==='declutter'&&isOB&&tf==='5m')continue;
    const x_=E.x[i],tk=tickOf(C.inst),top=E.p[i],bot=x_[0]*tk,end=x_[2]*60;if(end<dayStart||E.t[i]>dayEnd)continue;if(top<lo&&bot<lo||top>hi&&bot>hi)continue;
    const x0=xt(E.t[i]),x1=xtEnd(end);ctx.globalAlpha=alphaTF(tf);ctx.fillStyle=isOB?'rgba(176,124,224,.13)':'rgba(143,132,201,.10)';ctx.fillRect(x0,Y(top),x1-x0,Y(bot)-Y(top));
    ctx.strokeStyle=css(isOB?'--violet':'--purple');ctx.lineWidth=1;if(x_[4])ctx.setLineDash([4,3]);ctx.strokeRect(x0,Y(top),x1-x0,Y(bot)-Y(top));ctx.setLineDash([]);
    if(x1-x0>34){ctx.fillStyle=css(isOB?'--violet':'--purple');ctx.font='9.5px '+css('--mono');ctx.fillText((isOB?'OB ':'FVG ')+tf,x0+3,Y(top)+10)}ctx.globalAlpha=1;hit(5,x0,Y(top),x1,Y(bot),'event',i)}
  // pools
  if(LON.pools)for(const i of evsBack){if(E.k[i]!==KI.pool_formed)continue;const x_=E.x[i],pk=PKN[x_[2]],tf=TFN[E.tf[i]];if(pk==='session')continue;if(!visTF(tf))continue;if(C.mode==='declutter'&&tf==='5m'&&pk!=='eq')continue;
    const end=x_[3]*60,p=E.p[i];if(end<dayStart||E.t[i]>dayEnd||!inY(p))continue;const x0=Math.max(xt(E.t[i]),X(-.5)),x1=xtEnd(end);
    ctx.globalAlpha=alphaTF(tf)*(tf==='5m'?.55:.9);ctx.strokeStyle=css('--blue');ctx.lineWidth=tf==='1h'?1.6:1;if(pk==='eq')ctx.setLineDash([6,3]);ctx.beginPath();ctx.moveTo(x0,Y(p));ctx.lineTo(x1,Y(p));ctx.stroke();ctx.setLineDash([]);
    ctx.fillStyle=css('--blue');ctx.font='9.5px '+css('--mono');ctx.fillText(`${NAMES[x_[0]]} ${tf}`,Math.min(x1,pw-60)+2,Y(p)-3);ctx.globalAlpha=1;hit(3,x0,Y(p)-4,x1,Y(p)+4,'event',i)}
  // session levels
  if(LON.levels){const L=(D.levels[C.inst]||{})[C.day]||{};ctx.font='10px '+css('--mono');for(const[k,p]of Object.entries(L)){if(!inY(p))continue;ctx.strokeStyle=css(k.startsWith('P')?'--gold':'--gold2');ctx.globalAlpha=.85;ctx.setLineDash([7,4]);ctx.beginPath();ctx.moveTo(0,Y(p));ctx.lineTo(pw,Y(p));ctx.stroke();ctx.setLineDash([]);ctx.fillStyle=ctx.strokeStyle;ctx.textAlign='right';ctx.fillText(k,pw-4,Y(p)-3);ctx.textAlign='left';ctx.globalAlpha=1;hit(2,0,Y(p)-3,pw,Y(p)+3,'level',{name:k,price:p})}}
  // trades
  const dayTrades=TR.filter(t=>t.inst===C.inst&&t.sd===C.day&&t.walked);
  for(const t of dayTrades){const fired=t.fired,isOB=t.route==='ob';if(t.route==='busy')continue;if(t.route==='feed'&&!LON.seen)continue;if(isOB&&(!fired||!LON.obbook))continue;if(!isOB&&fired&&!LON.trades)continue;if(!isOB&&!fired&&!LON.seen)continue;
    const x0=xt(t.fill_t),x1=Math.max(x0+bw,xtEnd(t.exit_t)),ye=Y(t.entry),yt=Y(t.target),ys=Y(t.stop);
    if(fired){ctx.fillStyle=css('--upz');ctx.fillRect(x0,Math.min(ye,yt),x1-x0,Math.abs(yt-ye));ctx.fillStyle=css('--downz');ctx.fillRect(x0,Math.min(ye,ys),x1-x0,Math.abs(ys-ye));}
    ctx.strokeStyle=css(isOB?'--violet':'--up');ctx.lineWidth=fired?1.2:1;if(!fired)ctx.setLineDash([3,3]);ctx.globalAlpha=fired?1:.6;ctx.strokeRect(x0,Math.min(yt,ys),x1-x0,Math.abs(yt-ys));ctx.setLineDash([]);
    ctx.strokeStyle=css('--ink');ctx.beginPath();ctx.moveTo(x0,ye);ctx.lineTo(x1,ye);ctx.stroke();ctx.globalAlpha=1;
    ctx.font=(fired?'600 ':'')+'10.5px '+css('--mono');ctx.fillStyle=t.R>0?css('--up'):t.R<0?css('--down'):css('--muted');
    const lab=(t.route==='feed'?'◇ desk setup · ':t.route==='busy'?'busy · ':t.route==='orb'?'ORB ':fired?(isOB?'OB ':'★★ '):'○ skipped · ')+(t.side==='short'?'SELL':'BUY')+(isOB?'':' · '+t.grade)+' · '+fmtR(t.R);ctx.fillText(lab,x0+3,Math.min(yt,ys,ye)-5);
    hit(fired?8:6,x0,Math.min(yt,ys),x1,Math.max(yt,ys),'trade',t.idx)}
  // candles
  const up=css('--up'),dn=css('--down');for(let i=Math.max(0,Math.floor(v.i0));i<Math.min(B.n,Math.ceil(v.i1));i++){const x=X(i),c_=B.c[i]>=B.o[i]?up:dn;ctx.strokeStyle=c_;ctx.fillStyle=c_;ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x,Y(B.h[i]));ctx.lineTo(x,Y(B.l[i]));ctx.stroke();const y1=Y(Math.max(B.o[i],B.c[i])),y2=Y(Math.min(B.o[i],B.c[i]));ctx.fillRect(x-Math.max(.5,bw*.33),y1,Math.max(1,bw*.66),Math.max(1,y2-y1))}
  // structure breaks, swings, mss failed, idm
  ctx.font='9.5px '+css('--mono');
  for(const i of evs){const k=E.k[i],tf=TFN[E.tf[i]];if(!visTF(tf))continue;const p=E.p[i];if(!inY(p))continue;ctx.globalAlpha=alphaTF(tf);
    if(k===KI.structure_break&&LON.breaks){const x_=E.x[i];if(C.mode==='declutter'&&x_[0]===0)continue;const x0=xt(x_[3]*60),x1=xt(E.t[i]);ctx.strokeStyle=css(x_[0]===2?'--gold':'--ink');ctx.lineWidth=x_[0]===2?1.4:.9;ctx.beginPath();ctx.moveTo(x0,Y(p));ctx.lineTo(x1,Y(p));ctx.stroke();ctx.fillStyle=ctx.strokeStyle;ctx.fillText(BT[x_[0]]+(tf!=='5m'?' '+tf:''),(x0+x1)/2-12,Y(p)+(x_[1]>0?-3:10));hit(4,x0,Y(p)-4,x1,Y(p)+4,'event',i)}
    else if(k===KI.swing&&LON.swings){const lb=LABS[E.x[i]],isH=lb==='HH'||lb==='LH';ctx.fillStyle=css(tf==='5m'?'--faint':'--muted');const x=xt(E.t[i]);ctx.fillText(lb,x-6,Y(p)+(isH?-4:11));hit(2,x-7,Y(p)-12,x+9,Y(p)+12,'event',i)}
    else if(k===KI.mss_failed&&LON.mssf){const x=xt(E.t[i]);ctx.strokeStyle=css('--red');ctx.beginPath();ctx.moveTo(x-4,Y(p)-4);ctx.lineTo(x+4,Y(p)+4);ctx.moveTo(x+4,Y(p)-4);ctx.lineTo(x-4,Y(p)+4);ctx.stroke();hit(6,x-6,Y(p)-6,x+6,Y(p)+6,'event',i)}
    else if(k===KI.inducement&&LON.idm){const x_=E.x[i],x0=xt(E.t[i]),x1=xtEnd(x_[2]*60);ctx.strokeStyle=css('--muted');ctx.setLineDash([1,3]);ctx.beginPath();ctx.moveTo(x0,Y(p));ctx.lineTo(x1,Y(p));ctx.stroke();ctx.setLineDash([]);ctx.fillStyle=css('--muted');ctx.fillText('IDM',x0,Y(p)+(x_[0]>0?11:-3));hit(3,x0,Y(p)-4,x1,Y(p)+4,'event',i)}
    ctx.globalAlpha=1}
  // sweeps, smt, manip
  for(const i of evs){const k=E.k[i];const tf=TFN[E.tf[i]];
    if(k===KI.sweep&&LON.sweeps){const x_=E.x[i];if(!visTF(tf))continue;const c_=x_[3];if(C.mode==='declutter'&&(c_===2||tf==='5m'&&x_[2]!==2))continue;const ext=x_[5]*tickOf(C.inst),isH=x_[1]===1,x=xt(E.t[i]);if(!inY(ext))continue;const y=isH?Y(ext)-8:Y(ext)+8;
      ctx.beginPath();if(isH){ctx.moveTo(x,y+6);ctx.lineTo(x-5,y-3);ctx.lineTo(x+5,y-3)}else{ctx.moveTo(x,y-6);ctx.lineTo(x-5,y+3);ctx.lineTo(x+5,y+3)}ctx.closePath();
      ctx.strokeStyle=css('--gold');ctx.fillStyle=css('--gold');ctx.globalAlpha=alphaTF(tf);if(c_===0)ctx.fill();else if(c_===1){ctx.globalAlpha*=.45;ctx.fill();ctx.globalAlpha=alphaTF(tf);ctx.stroke()}else ctx.stroke();ctx.globalAlpha=1;hit(7,x-7,y-8,x+7,y+8,'event',i)}
    else if(k===KI.smt&&LON.smt){const isH=E.x[i][1]===1,x=xt(E.t[i]),j=bsearch(B.t,E.t[i]);if(j<0)continue;const y=isH?Y(B.h[j])-22:Y(B.l[j])+28;ctx.fillStyle=css('--cyan');ctx.font='600 10px '+css('--mono');ctx.textAlign='center';ctx.fillText('SMT',x,y);ctx.textAlign='left';hit(7,x-12,y-10,x+12,y+3,'event',i)}
    else if(k===KI.manip_leg&&LON.manip){const x=xt(E.t[i]),j=bsearch(B.t,E.t[i]);if(j<0)continue;ctx.strokeStyle=css('--red');ctx.lineWidth=1.2;ctx.strokeRect(x-bw*.5,Y(B.h[j])-2,bw,Y(B.l[j])-Y(B.h[j])+4);hit(5,x-bw*.5,Y(B.h[j]),x+bw*.5,Y(B.l[j]),'event',i)}}
  // selection highlight
  if(C.sel){const h_=HITS.find(h=>h.type===C.sel.type&&h.ref===C.sel.ref);if(h_){ctx.strokeStyle=css('--gold');ctx.lineWidth=1.5;ctx.setLineDash([2,2]);ctx.strokeRect(h_.x0-3,h_.y0-3,h_.x1-h_.x0+6,h_.y1-h_.y0+6);ctx.setLineDash([])}}
  // crosshair
  if(C.hover>=0&&C.hover<B.n){ctx.strokeStyle=css('--faint');ctx.setLineDash([2,3]);ctx.beginPath();ctx.moveTo(X(C.hover),T);ctx.lineTo(X(C.hover),T+ph);ctx.stroke();ctx.setLineDash([])}
  ctx.restore();
  C.geo={X,Y,bw,B,pw,T,ph,v};
  const j=C.hover>=0?C.hover:Math.min(B.n-1,Math.floor(v.i1)-1);if(j>=0&&j<B.n)$('#ohlc').innerHTML=`<b>${C.inst} ${C.tf}</b> · ${hhmm(B.t[j])} &nbsp; O <b>${px(B.o[j],C.inst)}</b> H <b>${px(B.h[j],C.inst)}</b> L <b>${px(B.l[j],C.inst)}</b> C <b class="${B.c[j]>=B.o[j]?'pos':'neg'}">${px(B.c[j],C.inst)}</b> V ${B.v[j].toLocaleString()}`}
function renderStats(B){const ev=dayEvents(0).length,tr=TR.filter(t=>t.inst===C.inst&&t.sd===C.day);const f=tr.filter(t=>t.fired&&t.route==='chain').length,ob=tr.filter(t=>t.fired&&t.route==='ob').length,seen=tr.filter(t=>t.route==='chain'&&!t.fired).length;
  $('#cStats').innerHTML=`<b>${B.n}</b> candles · <b>${ev}</b> things logged · <b>${f}</b> main ${f===1?'trade':'trades'} · <b>${ob}</b> order-block · ${seen} skipped`}
function renderLayers(){const evs=dayEvents(0),cnt={},tfc={};const add=(l,tf)=>{cnt[l]=(cnt[l]||0)+1;tfc[l]=tfc[l]||{};tfc[l][tf]=(tfc[l][tf]||0)+1};
  for(const i of evs){const k=KINDS[E.k[i]],tf=TFN[E.tf[i]];const map={pool_formed:PKN[(E.x[i]||[])[2]]==='session'?null:'pools',sweep:'sweeps',manip_leg:'manip',smt:'smt',inducement:'idm',swing:'swings',structure_break:'breaks',mss_failed:'mssf',ob_formed:'ob',fvg_formed:'fvg',fvg_inverted:'fvg',session_open:'sess'};const l=map[k];if(l)add(l,tf)}
  const tr=TR.filter(t=>t.inst===C.inst&&t.sd===C.day&&t.walked);cnt.trades=tr.filter(t=>t.fired&&t.route==='chain').length;cnt.seen=tr.filter(t=>!t.fired&&t.route==='chain').length;cnt.obbook=tr.filter(t=>t.fired&&t.route==='ob').length;cnt.levels=Object.keys((D.levels[C.inst]||{})[C.day]||{}).length;
  $('#layers').innerHTML=LAYERS.map(([id,nm,c])=>`<label class="lrow"><input type="checkbox" data-l="${id}" ${LON[id]?'checked':''}><span><span class="nm"><span class="dotk" style="background:var(${c})"></span>${nm}</span>${tfc[id]?`<span class="tfs">${Object.entries(tfc[id]).map(([a,b])=>a+' '+b).join('  ')}</span>`:''}</span><span class="ct2">${cnt[id]||0}</span></label>`).join('');
  $$('#layers input').forEach(x=>x.onchange=()=>{LON[x.dataset.l]=x.checked;draw()});
  const tfAll={};for(const i of evs){const tf=TFN[E.tf[i]];if(tf!=='session')tfAll[tf]=(tfAll[tf]||0)+1}
  $('#tfchips').innerHTML=['5m','15m','1h'].map(tf=>`<button type="button" class="tfchip ${C.tfvis[tf]}" data-tf="${tf}">${C.tfvis[tf]==='bright'?'●':C.tfvis[tf]==='ghost'?'○':'×'} ${tf} · ${tfAll[tf]||0}</button>`).join('');
  $$('#tfchips .tfchip').forEach(b=>b.onclick=()=>{const o=['bright','ghost','hidden'];C.tfvis[b.dataset.tf]=o[(o.indexOf(C.tfvis[b.dataset.tf])+1)%3];renderLayers();draw()})}
// interaction
const ptrs=new Map();let drag=null,pinch=null,moved=false;
cv.addEventListener('pointerdown',e=>{cv.setPointerCapture(e.pointerId);ptrs.set(e.pointerId,{x:e.offsetX,y:e.offsetY});moved=false;if(ptrs.size===1)drag={x:e.offsetX,v:{...C.view}};if(ptrs.size===2){const [a,b]=[...ptrs.values()];pinch={d:Math.abs(a.x-b.x)||1,v:{...C.view},cx:(a.x+b.x)/2};drag=null}});
cv.addEventListener('pointermove',e=>{if(!C.geo)return;const g=C.geo;if(ptrs.has(e.pointerId))ptrs.set(e.pointerId,{x:e.offsetX,y:e.offsetY});
  if(pinch&&ptrs.size===2){const [a,b]=[...ptrs.values()];const d=Math.abs(a.x-b.x)||1,f=pinch.d/d,span=(pinch.v.i1-pinch.v.i0)*f,cj=pinch.v.i0+pinch.cx/g.bw*((pinch.v.i1-pinch.v.i0)/(g.pw/g.bw));const r=pinch.cx/g.pw;C.view={i0:cj-span*r,i1:cj+span*(1-r)};moved=true;draw();return}
  if(drag){const dx=e.offsetX-drag.x;if(Math.abs(dx)>4)moved=true;if(moved){const sh=dx/g.bw;C.view={i0:drag.v.i0-sh,i1:drag.v.i1-sh};draw();return}}
  const j=Math.floor(g.v.i0+e.offsetX/g.bw);if(j!==C.hover){C.hover=j;draw()}});
const endP=e=>{ptrs.delete(e.pointerId);if(ptrs.size<2)pinch=null;if(ptrs.size===0){if(!moved&&drag)clickAt(e.offsetX,e.offsetY);drag=null}};
cv.addEventListener('pointerup',endP);cv.addEventListener('pointercancel',endP);
cv.addEventListener('pointerleave',()=>{if(!ptrs.size){C.hover=-1;draw()}});
cv.addEventListener('wheel',e=>{if(!C.geo)return;e.preventDefault();const g=C.geo,f=e.deltaY>0?1.15:1/1.15,span=(g.v.i1-g.v.i0)*f,cj=g.v.i0+e.offsetX/g.bw,r=e.offsetX/g.pw;C.view={i0:cj-span*r,i1:cj+span*(1-r)};draw()},{passive:false});
addEventListener('keydown',e=>{if($('#chart').hidden||/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName))return;if(e.key==='ArrowLeft')stepDay(-1);else if(e.key==='ArrowRight')stepDay(1);else if(e.key==='0'){C.view=null;draw()}else if(e.key==='+'||e.key==='='){const v=C.view,c=(v.i0+v.i1)/2,s=(v.i1-v.i0)/1.3;C.view={i0:c-s/2,i1:c+s/2};draw()}else if(e.key==='-'){const v=C.view,c=(v.i0+v.i1)/2,s=(v.i1-v.i0)*1.3;C.view={i0:c-s/2,i1:c+s/2};draw()}});
function clickAt(x,y){const c=HITS.filter(h=>x>=h.x0-2&&x<=h.x1+2&&y>=h.y0-2&&y<=h.y1+2).sort((a,b)=>b.pri-a.pri||((a.x1-a.x0)*(a.y1-a.y0))-((b.x1-b.x0)*(b.y1-b.y0)));
  if(c.length)C.sel={type:c[0].type,ref:c[0].ref};else{const g=C.geo;const j=Math.floor(g.v.i0+x/g.bw);if(j>=0&&j<g.B.n)C.sel={type:'candle',ref:j};else C.sel=null}
  renderInspector();draw();if(innerWidth<980)$('#insp').scrollIntoView({block:'nearest',behavior:'smooth'})}
