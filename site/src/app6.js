// ================= journal store, Claude, export
let JR={},REVIEWS=[];const STORE={mode:'none',uid:null,db:null};const CAP={sample:null,downloads:null};
const docId=id=>'n_'+id.replace(/[^A-Za-z0-9_-]/g,'_').slice(0,80)+'_'+[...id].reduce((h,c)=>(h*31+c.charCodeAt(0))>>>0,7).toString(36);
try{const raw=localStorage.getItem('argon2-journal');if(raw){const o=JSON.parse(raw);JR=o.j||{};REVIEWS=o.r||[];STORE.mode='local'}else STORE.mode='local'}catch(e){STORE.mode='none'}
function persistLocal(){try{localStorage.setItem('argon2-journal',JSON.stringify({j:JR,r:REVIEWS}))}catch(e){}}
async function saveJ(id,patch){JR[id]={...(JR[id]||{}),...patch,updated:Date.now()};const s=$('#js');
  if(STORE.mode==='db'){try{await STORE.db.collection('data/users/'+STORE.uid).doc(docId(id)).set({type:'note',note:id,...JR[id]});if(s)s.textContent='Saved to your Argon journal. Claude can read it.'}catch(e){persistLocal();if(s)s.textContent='Couldn\'t reach the journal, so it\'s saved on this device.'}}
  else{persistLocal();if(s)s.textContent=STORE.mode==='local'?'Saved on this device only.':'Not saved: storage is blocked here.'}}
async function initCaps(){const CL=window.claude;if(!CL||!CL.use)return;
  try{const [db,user,sample,dl]=await Promise.all([CL.use('db'),CL.use('user'),CL.use('sample'),CL.use('downloads')]);CAP.sample=sample;CAP.downloads=dl;
    if(db&&user){const uid=await user.id();if(uid){STORE.db=db;STORE.uid=uid;const q=await db.collection('data/users/'+uid).get();const fromDb={};const rv=[];
      for(const d of q.docs){const x=d.data();if(!x)continue;if(x.type==='note'&&x.note)fromDb[x.note]={text:x.text,verdict:x.verdict,updated:x.updated};if(x.type==='review')rv.push({id:x.id,text:x.text,at:x.at})}
      // carry over anything only on this device
      for(const[k,v]of Object.entries(JR))if(!fromDb[k]){fromDb[k]=v;db.collection('data/users/'+uid).doc(docId(k)).set({type:'note',note:k,...v}).catch(()=>{})}
      JR=fromDb;REVIEWS=rv.sort((a,b)=>a.at<b.at?-1:1);STORE.mode='db'}}}catch(e){}
  buildNotes();renderTree();if(NOTE&&!GRAPH.on&&!$('#studies').hidden)openNote(NOTE)}
async function askClaude(){const out=$('#aiout'),btn=$('#askBtn');if(!CAP.sample)return;out.hidden=false;out.textContent='Claude is reading your notes…';btn.disabled=true;
  const brief=t=>({id:TNOTE.get(t.idx),route:t.route,inst:t.inst,side:t.side,win:t.win,family:t.family,grade:t.grade,score:t.score,smt:t.smt,bias_1h:t.bias,premium_discount_ok:t.pd,R:t.R,mfe:t.mfe,mae:t.mae,status:t.status,hour:t.hour,dow:DOW[t.dow]});
  const walked=TR.filter(t=>t.route==='chain'&&t.walked);const refs={};for(const k of['1','2','3','4','5']){const s=stats(walked.filter(t=>!t.fired&&t.failed[0]===k));refs['step'+k]={n:s.n,gross:+s.g.toFixed(2),winrate:+s.wr.toFixed(2)}}
  const fam={};for(const[k,s]of bucket(walked,t=>setupKey(t)))fam[k]={n:s.n,avgR:+s.avg.toFixed(2),gross:+s.g.toFixed(2)};
  const notes=Object.entries(JR).filter(([k,v])=>v.text||v.verdict).map(([k,v])=>{const e=[...TNOTE].find(([i,id])=>id===k);return {note:k,verdict:v.verdict||null,text:(v.text||'').slice(0,600),trade_R:e?TR[e[0]].R:null}});
  const payload={engine_sig:D.sig,days:DAYS.length,rules:NOTES.get(RB).md,lit_chain:stats(FIRED),ob_book:stats(OBB),fired_trades:FIRED.map(brief),ob_book_trades:OBB.map(brief),refused_but_walked_by_step:refs,families:fam,user_journal:notes};
  const prompt=`You are reviewing a trading research journal for a student building a paper-trading bot (Argon v2) that trades liquidity sweeps (price poking past key highs and lows, then reversing) on NQ, ES and gold futures. The data is a replay of real 5-minute bars; R is gross R-multiples. Be honest and specific, quote numbers, and say plainly when a sample is too small to mean anything.\n\nWrite plain text with these short headings: Where the edge is strongest. What is draining. Contradictions in the rules. Gaps in the data or the thinking. Patterns in my own calls (compare my verdicts and notes with what the trades did; if there are none, say what to start logging). Three rule changes to test in v0.3.\n\nUnder 450 words. No preamble.\n\nDATA:\n${JSON.stringify(payload)}`;
  try{const r=await CAP.sample(prompt,{modelTier:'complex',onText:({text})=>{out.textContent=text}});out.textContent=r.text;
    const at=new Date().toISOString().slice(0,16).replace('T',' ');const id=`Claude review — ${at}`;const rev={id,text:r.text,at};REVIEWS.push(rev);
    if(STORE.mode==='db'){try{await STORE.db.collection('data/users/'+STORE.uid).doc('review_'+Date.now()).set({type:'review',...rev})}catch(e){persistLocal()}}else persistLocal();
    addNote(id,'Reviews',`---\ntype: claude-review\nwritten: ${at}\n---\n# ${id}\n\n${r.text}\n\nBuilt from [[Edge report]] and your journal.`);renderTree()}
  catch(e){out.textContent=e&&e.code==='not_granted'?'Permission to ask Claude was turned down.':e&&e.code==='rate_limited'?'Too many requests. Try again in a minute.':'The review didn\'t finish. '+(e&&e.message||'')}
  btn.disabled=false}
function exportFiles(){const files=[{path:'README.md',content:`# Argon v2 notes\n\nDownloaded from Argon v2. Open this folder in Obsidian as a vault. Good places to start: [[${RB}]], [[Lessons]] and [[Edge report]].\n`}];
  for(const n of NOTES.values()){let md=n.md;const j=JR[n.id];if(j&&(j.text||j.verdict))md+=`\n## My notes\n\n${j.verdict?`Verdict: **${j.verdict}**\n\n`:''}${j.text||''}\n`;files.push({path:`${n.folder}/${n.id.replace(/[\\/:*?"<>|]/g,'-')}.md`,content:md})}return files}
window.__exportFiles=exportFiles;
async function exportVault(){const b=$('#xBtn');b.textContent='preparing…';try{if(!window.JSZip)await new Promise((ok,no)=>{const s=document.createElement('script');s.src='https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';s.onload=ok;s.onerror=no;document.head.appendChild(s)});
  const z=new JSZip();for(const f of exportFiles())z.file('Argon v2/'+f.path,f.content);const blob=await z.generateAsync({type:'blob'});await CAP.downloads.save({filename:'argon-v2-vault.zip',data:blob});b.textContent='download notes'}
  catch(e){b.textContent=e&&e.code==='declined'?'download notes':'download failed';setTimeout(()=>b.textContent='download notes',2500)}}
// ================= GRAPH
function showGraph(){$('#notepane').innerHTML=`<div class="nbar"><span class="path">map of all ${NOTES.size} notes</span><span class="sp"></span><span class="note-s">drag to move · pinch or scroll to zoom · tap a dot to open it</span></div><canvas id="graph"></canvas><div class="legendline" style="margin-top:8px">${[['Days','--gold'],['Trades','--up'],['Setups','--violet'],['Ideas','--cyan'],['Rules','--ink'],['Reviews','--blue']].map(([f,c])=>`<span><span class="dotk" style="background:var(${c})"></span>${f}</span>`).join('')}</div>`;
  layoutGraph();fitGraph();drawGraph();const g=$('#graph');let dr=null,mv=false;const ps=new Map();let pin=null;
  g.onpointerdown=e=>{g.setPointerCapture(e.pointerId);ps.set(e.pointerId,[e.offsetX,e.offsetY]);mv=false;dr={x:e.offsetX,y:e.offsetY,ox:GRAPH.ox,oy:GRAPH.oy};if(ps.size===2){const [a,b]=[...ps.values()];pin={d:Math.hypot(a[0]-b[0],a[1]-b[1]),s:GRAPH.s};dr=null}};
  g.onpointermove=e=>{if(ps.has(e.pointerId))ps.set(e.pointerId,[e.offsetX,e.offsetY]);if(pin&&ps.size===2){const [a,b]=[...ps.values()];GRAPH.s=pin.s*Math.hypot(a[0]-b[0],a[1]-b[1])/pin.d;mv=true;drawGraph();return}
    if(dr&&ps.size===1){const dx=e.offsetX-dr.x,dy=e.offsetY-dr.y;if(Math.hypot(dx,dy)>4)mv=true;if(mv){GRAPH.ox=dr.ox+dx;GRAPH.oy=dr.oy+dy;drawGraph()}}else{const n=nodeAt(e.offsetX,e.offsetY);if(n!==GRAPH.hov){GRAPH.hov=n;drawGraph()}}};
  g.onpointerup=e=>{ps.delete(e.pointerId);if(ps.size<2)pin=null;if(!mv&&ps.size===0){const n=nodeAt(e.offsetX,e.offsetY);if(n)openNote(n.id)}if(!ps.size)dr=null};
  g.onwheel=e=>{e.preventDefault();GRAPH.s*=e.deltaY>0?.9:1.1;drawGraph()}}
function layoutGraph(){if(GRAPH.nodes&&GRAPH.n===NOTES.size)return;const ids=[...NOTES.keys()],ix=new Map(ids.map((id,i)=>[id,i]));const fi={Daily:0,Trades:1,Setups:2,Concepts:3,Rules:4,Reviews:5};
  const nodes=ids.map((id,i)=>{const f=NOTES.get(id).folder,a=fi[f]/6*Math.PI*2;return {id,f,x:Math.cos(a)*200+Math.random()*80-40,y:Math.sin(a)*200+Math.random()*80-40,vx:0,vy:0,deg:0}});
  const edges=[];for(const n of NOTES.values())for(const l of new Set(linksOf(n.md)))if(ix.has(l)&&l!==n.id){edges.push([ix.get(n.id),ix.get(l)]);nodes[ix.get(n.id)].deg++;nodes[ix.get(l)].deg++}
  for(let it=0;it<260;it++){const k=1-it/260;for(let i=0;i<nodes.length;i++){const a=nodes[i];for(let j=i+1;j<nodes.length;j++){const b=nodes[j];let dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy+.01;if(d2>90000)continue;const f=420/d2;a.vx+=dx*f;a.vy+=dy*f;b.vx-=dx*f;b.vy-=dy*f}}
    for(const[i,j]of edges){const a=nodes[i],b=nodes[j],dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1,f=(d-60)*.012;a.vx+=dx/d*f;a.vy+=dy/d*f;b.vx-=dx/d*f;b.vy-=dy/d*f}
    for(const n of nodes){n.vx-=n.x*.004;n.vy-=n.y*.004;n.x+=Math.max(-20,Math.min(20,n.vx))*k;n.y+=Math.max(-20,Math.min(20,n.vy))*k;n.vx*=.5;n.vy*=.5}}
  GRAPH.nodes=nodes;GRAPH.edges=edges;GRAPH.n=NOTES.size;GRAPH.s=.9;GRAPH.ox=0;GRAPH.oy=0}
function fitGraph(){const g=$('#graph');if(!g)return;const r=g.getBoundingClientRect();let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;for(const n of GRAPH.nodes){x0=Math.min(x0,n.x);x1=Math.max(x1,n.x);y0=Math.min(y0,n.y);y1=Math.max(y1,n.y)}GRAPH.s=Math.min((r.width-60)/(x1-x0||1),(r.height-60)/(y1-y0||1));GRAPH.ox=-(x0+x1)/2*GRAPH.s;GRAPH.oy=-(y0+y1)/2*GRAPH.s}
function drawGraph(){const g=$('#graph');if(!g)return;const r=g.getBoundingClientRect(),dpr=devicePixelRatio||1;g.width=r.width*dpr;g.height=r.height*dpr;const c=g.getContext('2d');c.setTransform(dpr,0,0,dpr,0,0);
  const cx=r.width/2+GRAPH.ox,cy=r.height/2+GRAPH.oy,s=GRAPH.s;const P=n=>[cx+n.x*s,cy+n.y*s];const N=GRAPH.nodes;const cur=N.findIndex(n=>n.id===NOTE);
  const nb=new Set();for(const[i,j]of GRAPH.edges){if(i===cur)nb.add(j);if(j===cur)nb.add(i)}
  c.lineWidth=.6;for(const[i,j]of GRAPH.edges){const [x1,y1]=P(N[i]),[x2,y2]=P(N[j]);c.strokeStyle=(i===cur||j===cur)?css('--gold'):css('--line');c.globalAlpha=(i===cur||j===cur)?.9:.55;c.beginPath();c.moveTo(x1,y1);c.lineTo(x2,y2);c.stroke()}c.globalAlpha=1;
  const colF={Daily:'--gold',Setups:'--violet',Concepts:'--cyan',Rules:'--ink',Reviews:'--blue'};
  for(let i=0;i<N.length;i++){const n=N[i],[x,y]=P(n);let col;if(n.f==='Trades'){const e=[...TNOTE].find(([k,id])=>id===n.id);col=e&&TR[e[0]].R>0?css('--up'):css('--down')}else col=css(colF[n.f]);
    const rad=Math.min(9,2.5+Math.sqrt(n.deg)*.9)*(i===cur?1.6:1);c.fillStyle=col;c.beginPath();c.arc(x,y,rad,0,7);c.fill();if(i===cur){c.strokeStyle=css('--gold');c.lineWidth=2;c.stroke()}
    if(n.f==='Concepts'||n.f==='Rules'||n.f==='Reviews'||i===cur||nb.has(i)||GRAPH.hov===n||(s>1.6)){c.fillStyle=css(i===cur||GRAPH.hov===n?'--ink':'--muted');c.font='10.5px '+css('--mono');c.fillText(n.id,x+rad+3,y+3)}}}
function nodeAt(x,y){const g=$('#graph');if(!g||!GRAPH.nodes)return null;const r=g.getBoundingClientRect(),cx=r.width/2+GRAPH.ox,cy=r.height/2+GRAPH.oy;let best=null,bd=144;for(const n of GRAPH.nodes){const d=(cx+n.x*GRAPH.s-x)**2+(cy+n.y*GRAPH.s-y)**2;if(d<bd){bd=d;best=n}}return best}
// ================= EVENTS TAB
const GROUPS={All:null,'Levels and traps':['pool_formed','sweep','manip_leg','smt'],Trend:['swing','structure_break','mss_failed','inducement'],Gaps:['fvg_formed','fvg_inverted'],'Order blocks':['ob_formed','ob_mitigated','ob_invalidated'],Times:['session_open'],Trades:['fire','ob_entry','refusal','outcome']};
const EF={g:'Trades',kind:'',inst:'',tf:'',day:'',q:'',lim:200};
function renderEventFilters(){$('#efil1').innerHTML=Object.keys(GROUPS).map(g=>`<button class="chip" data-g="${g}" aria-pressed="${EF.g===g}">${g}</button>`).join('')+`<select id="ek" aria-label="Kind"><option value="">every type</option>${KINDS.map(k=>`<option value="${k}" ${EF.kind===k?'selected':''}>${FN[k]}</option>`).join('')}</select>`;
  $('#efil2').innerHTML=`<select id="ei" aria-label="Instrument"><option value="">all markets</option>${D.insts.map(s=>`<option ${EF.inst===s?'selected':''}>${s}</option>`).join('')}</select><select id="etf" aria-label="Timeframe"><option value="">every chart</option>${TFN.map(t=>`<option ${EF.tf===t?'selected':''}>${t}</option>`).join('')}</select><select id="ed" aria-label="Day"><option value="">all ${DAYS.length} days</option>${DAYS.slice().reverse().map(d=>`<option ${EF.day===d?'selected':''}>${d}</option>`).join('')}</select><input type="search" id="eq" placeholder="search" value="${esc(EF.q)}" aria-label="Search the log">`;
  $$('#efil1 [data-g]').forEach(b=>b.onclick=()=>{EF.g=b.dataset.g;EF.kind='';EF.lim=200;renderEventFilters();renderEvents()});
  $('#ek').onchange=e=>{EF.kind=e.target.value;EF.lim=200;renderEvents()};$('#ei').onchange=e=>{EF.inst=e.target.value;EF.lim=200;renderEvents()};$('#etf').onchange=e=>{EF.tf=e.target.value;EF.lim=200;renderEvents()};$('#ed').onchange=e=>{EF.day=e.target.value;EF.lim=200;renderEvents()};
  let tm;$('#eq').oninput=e=>{clearTimeout(tm);tm=setTimeout(()=>{EF.q=e.target.value;EF.lim=200;renderEvents()},250)}}
function renderEvents(){const gk=GROUPS[EF.g]?new Set(GROUPS[EF.g].map(k=>KI[k])):null,kk=EF.kind?KI[EF.kind]:-1,ii=EF.inst?INSTS.indexOf(EF.inst):-1,tf=EF.tf?TFN.indexOf(EF.tf):-1,q=EF.q.toLowerCase();
  const sel=[];for(let i=E.n-1;i>=0;i--){if(gk&&!gk.has(E.k[i]))continue;if(kk>=0&&E.k[i]!==kk)continue;if(ii>=0&&E.inst[i]!==ii)continue;if(tf>=0&&E.tf[i]!==tf)continue;if(EF.day&&E.sd[i]!==EF.day)continue;sel.push(i)}
  let rows=sel;if(q){rows=[];for(const i of sel){const o=evObj(i);if((FN[o.kind]+' '+evText(o)).toLowerCase().includes(q))rows.push(i);if(rows.length>=EF.lim+1)break}}
  $('#ecount').textContent=`${q?(rows.length>EF.lim?'more than '+EF.lim:rows.length):sel.length.toLocaleString()} things logged · newest first · tap one to see it on the chart`;
  $('#elist').innerHTML=`<div class="erow ehead"><span class="d">day</span><span>time</span><span>market</span><span class="tfc">chart</span><span>type</span><span class="tx">what happened</span></div>`+rows.slice(0,EF.lim).map(i=>{const o=evObj(i);return `<div class="erow" data-i="${i}" tabindex="0"><span class="d dim">${o.day}</span><span>${hhmm(o.t)}</span><span class="${o.inst==='GC'?'gold':''}">${o.inst}</span><span class="tfc dim">${o.tf}</span><span><span class="dotk" style="background:var(${KC[o.kind]})"></span>${FN[o.kind]}</span><span class="tx">${esc(evText(o))}</span></div>`}).join('');
  $('#emore').hidden=rows.length<=EF.lim;
  $$('#elist .erow[data-i]').forEach(r=>{const go=()=>{const o=evObj(+r.dataset.i);const sel_=o.tradeIdx!=null?{type:'trade',ref:o.tradeIdx}:{type:'event',ref:o.id};gotoChart(o.inst,o.day,o.t,sel_)};r.onclick=go;r.onkeydown=e=>{if(e.key==='Enter')go()}})}
$('#emore').onclick=()=>{EF.lim+=200;renderEvents()};
