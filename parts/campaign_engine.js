/* ================================================================
   CAMPAIGN ENGINE: features, story dialogue, objectives, duel
   ================================================================ */
function featureOn(f){ const v=MAP&&MAP[f]; if(v==='castle2') return S.castle>=2; if(f==='expedition') return !!v&&S.objs.some(o=>o.t==='cave'); return !!v; }
const isCamp=()=>!!(MAP&&MAP.campaign);
const chapterOf=id=>CAMPAIGN.find(c=>c.id===id);
const curChapter=()=>isCamp()?chapterOf(S.map):null;

// ---------- dialogue ----------
let story=null; // {lines,i,shown,full,typing,done,timer}
const storyOn=()=>!!story;
function playScript(lines,done){ if(!lines||!lines.length){ done&&done(); return; } if(story){ const prev=story.done; story.lines=story.lines.concat(lines); story.done=()=>{ prev&&prev(); done&&done(); }; return; }
 story={lines:lines.slice(),i:-1,done}; closePop(); cancelPlace(true); $('story').hidden=false; document.body.classList.add('storying'); nextLine(); }
function portraitHTML(w){ const c=CHAR[w]; if(!c||!c.spr||typeof SPRITE_DATA==='undefined'||!SPRITE_DATA[c.spr]) return ''; return `<img src="${SPRITE_DATA[c.spr].d}" alt="${c.name}">`; }
function nextLine(){ const st=story; st.i++; if(st.i>=st.lines.length){ endStory(); return; } const ln=st.lines[st.i], c=CHAR[ln.w]||CHAR.narr;
 const el=$('story'); el.className='story'+(ln.w==='narr'?' narr':'')+(ln.w==='mueum'?' mueum':''); el.querySelector('.sp').innerHTML=portraitHTML(ln.w);
 el.querySelector('.who').innerHTML=c.name?`<b>${c.name}</b><span>${c.role}</span>`:''; st.full=ln.t; st.shown=0; st.typing=!!ln.type; clearInterval(st.timer);
 const tx=el.querySelector('.say'); tx.textContent=''; st.timer=setInterval(()=>{ st.shown=Math.min(st.full.length,st.shown+2); tx.textContent=st.full.slice(0,st.shown); if(st.shown>=st.full.length){ clearInterval(st.timer); afterReveal(); } },22);
 el.querySelector('.hint').innerHTML=''; AU.tone(ln.w==='mueum'?220:660,'sine',0.03,0.05); }
function afterReveal(){ const st=story, ln=st.lines[st.i];
 if(ln.type){ $('story').querySelector('.hint').innerHTML=`아래에 그대로 쓰고 <kbd>Space</kbd>`; askType(ln.type,'story',ok=>{ if(!story) return; nextLine(); }); }
 else $('story').querySelector('.hint').innerHTML=`<kbd>Enter</kbd> 다음`; }
function advanceStory(){ const st=story; if(!st) return; if(st.shown<st.full.length){ clearInterval(st.timer); st.shown=st.full.length; $('story').querySelector('.say').textContent=st.full; afterReveal(); return; } if(st.typing) return; nextLine(); }
function endStory(){ const d=story&&story.done; clearInterval(story&&story.timer); story=null; $('story').hidden=true; document.body.classList.remove('storying'); if(T.special==='story'){ T.special=null; setMode(T.prevMode||'word',true); T.prevMode=null; } refocus(); d&&d(); }

// ---------- typed prompts (story, restore ruins, wake stones) ----------
let askCb=null;
function askType(text,kind,cb){ askCb=cb; T.prevMode=T.prevMode||T.mode; T.special=kind; T.target=text; resetInput(); renderDockTop(); $('hint').innerHTML='<kbd>Space</kbd> 또는 <kbd>Enter</kbd> 완성';
 const label=kind==='restore'?'무너진 집의 이름을 다시 써요':kind==='stone'?'비석에 새겨진 문장':kind==='duel'?'무음에게 답하기':'이야기 속 문장';
 txBody.className=''; txBody.innerHTML=`<div class="head"><span><b>${label}</b></span><span>정확도 80% 이상이면 통과</span></div><div class="cur" id="cur"></div>`; buildSpans($('cur')); renderTyped(); renderNums(); refocus(); }
function promptSubmit(acc,perfect){ const kind=T.special, cb=askCb;
 if(kind==='duel'){ duelAnswer(acc,perfect); return; }
 if(acc<0.8){ errorFx(); showGrade('다시 한 번'); resetInput(); renderTyped(); return; }
 showGrade(perfect?'PERFECT':'좋아요'); AU.pluck(5); burstAt(caretPoint(),perfect); askCb=null;
 if(kind!=='story'){ T.special=null; setMode(T.prevMode||'word',true); T.prevMode=null; } else { resetInput(); }
 cb&&cb(true); }
function restoreRuin(o){ closePop(); askType(o.word,'restore',()=>{ const i=S.objs.indexOf(o); if(i<0) return; S.objs.splice(i,1,{t:o.becomes,gx:o.gx,gy:o.gy,sz:1,seed:o.seed,born:performance.now()}); S.stats.restored=(S.stats.restored||0)+1; dirty(); puff(o.gx,o.gy,20); sparkle(o.gx,o.gy,16); AU.build(); setTimeout(()=>AU.chime(),200); floatText(o.gx,o.gy,'복원!','#ffe08a'); syncFolk(); afterProgress(); }); }
function wakeStone(o){ closePop(); askType(o.word,'stone',()=>{ o.awake=true; sparkle(o.gx,o.gy,20); AU.fanfare(); floatText(o.gx,o.gy,'비석이 깨어났다','#ffe08a'); afterProgress(); }); }

// ---------- objectives ----------
function checkObjectives(){ const ch=curChapter(); if(!ch||!S.camp||S.camp.won) return; let newly=[];
 ch.goals.forEach(gl=>{ if(S.camp.done[gl.id]) return; if(gl.prog()>=gl.goal){ S.camp.done[gl.id]=true; newly.push(gl); } });
 newly.forEach(gl=>{ toastGoal(gl.text); if(ch.on&&ch.on[gl.id]) setTimeout(()=>playScript(ch.on[gl.id]),600); });
 renderObjTrack();
 if(ch.goals.every(gl=>S.camp.done[gl.id])&&!S.camp.won){ S.camp.won=true; setTimeout(()=>finishChapter(ch),newly.length?1800:300); } }
function toastGoal(t){ const el=document.createElement('div'); el.className='toast'; el.innerHTML=`<div class="ic">${PH.check}</div><div><small>목표 완료</small><b>${t}</b></div>`; $('toasts').appendChild(el); AU.chime(); setTimeout(()=>{ el.classList.add('out'); setTimeout(()=>el.remove(),450); },3500); }
function renderObjTrack(){ const el=$('objTrack'), ch=curChapter(); if(!ch||!started){ el.hidden=true; return; } el.hidden=false;
 el.innerHTML=`<div class="oh"><b>${ch.no}장 ${ch.title}</b><button class="x" id="objFold" aria-label="접기">${S.camp.fold?PH.plus:PH.minus}</button></div>`+(S.camp.fold?'':ch.goals.map(gl=>{ const v=Math.min(gl.goal,gl.prog()), d=S.camp.done[gl.id]; return `<div class="og ${d?'done':''}"><i>${d?PH.check:''}</i><span>${gl.text}</span><em>${gl.goal>1?`${v}/${gl.goal}`:''}</em></div>`; }).join(''));
 $('objFold').onclick=()=>{ S.camp.fold=!S.camp.fold; renderObjTrack(); refocus(); }; }
function chapterStars(ch){ const acc=S.camp.accN?S.camp.accSum/S.camp.accN:1; return 1+(acc>=0.9?1:0)+(ch.star3.ok()?1:0); }
function finishChapter(ch){ const stars=chapterStars(ch), acc=S.camp.accN?Math.round(100*S.camp.accSum/S.camp.accN):100;
 const prev=(P.camp.done[ch.id]||{}).stars||0; P.camp.done[ch.id]={stars:Math.max(prev,stars)}; saveProfile(); save();
 playScript(ch.outro,()=>{ AU.fanfare(); confetti(160);
  const next=CAMPAIGN[CAMPAIGN.indexOf(ch)+1];
  showModal(`<div class="vic"><small>${ch.no}장 완료</small><b>${ch.title}</b><div class="stars">${[1,2,3].map(i=>`<i class="${i<=stars?'on':''}">${PH.sparkle}</i>`).join('')}</div>
   <ul class="checks"><li class="ok">${PH.check}목표 모두 달성</li><li class="${acc>=90?'ok':''}">${PH.check}평균 정확도 90% 이상 (지금 ${acc}%)</li><li class="${ch.star3.ok()?'ok':''}">${PH.check}${ch.star3.text}</li></ul>
   <div class="foot"><button class="btn" data-m="stay">이 섬 계속 꾸미기</button><button class="btn primary" data-m="map">${next?`다음 장: ${next.title}`:'캠페인 지도'}</button></div></div>`,
   k=>{ if(k==='map') openCampaign(next?next.id:null); });
  if(ch.id==='ch6'&&!P.endingSeen){ P.endingSeen=true; saveProfile(); }
 }); }

// ---------- final duel ----------
let duel=null;
function startDuel(){ const ch=curChapter(); if(!ch) return; if(S.objs.filter(o=>o.t==='wordstone'&&!o.awake).length){ toast('비석 세 개를 먼저 깨워야 탑의 문이 열려요'); return; }
 if(S.camp.duelWon){ toast('무음은 이제 말과 말 사이에 머물고 있어요'); return; }
 closePop(); closeDrawer(); duel={i:0,hp:DUEL.length,limit:0,left:0}; AU.horn(); $('duel').hidden=false; duelStep(); }
function duelStep(){ const d=DUEL[duel.i]; duel.limit=(6+strokesOf(d.a)*0.62); duel.left=duel.limit+1.2; renderDuel(); askType(d.a,'duel',null); }
function renderDuel(){ const el=$('duel'); if(!duel){ el.hidden=true; return; } const d=DUEL[Math.min(duel.i,DUEL.length-1)];
 el.innerHTML=`<div class="dp">${portraitHTML('mueum')}</div><div class="dt"><small>침묵왕 무음</small><p>${d.m}</p><div class="hp">${DUEL.map((_,i)=>`<i class="${i<duel.i?'gone':''}"></i>`).join('')}</div><div class="timer"><b id="duelTimer"></b></div></div>`; }
function stepDuel(dt){ if(!duel||T.special!=='duel') return; duel.left-=dt/1000; const b=$('duelTimer'); if(b){ b.style.transform=`scaleX(${Math.max(0,Math.min(1,duel.left/duel.limit))})`; b.style.background=duel.left<duel.limit*.25?'var(--bad)':''; }
 if(duel.left<=0){ S.camp.duelFails++; errorFx(); showGrade('안개가 짙어졌다'); toast('시간이 다 됐어요. 같은 문장을 다시 써 봐요'); duel.left=duel.limit+2; resetInput(); renderTyped(); } }
function duelAnswer(acc,perfect){ if(acc<0.8){ errorFx(); showGrade('다시 한 번'); resetInput(); renderTyped(); return; }
 AU.zap(); AU.pluck(duel.i+3); showGrade(perfect?'PERFECT':'닿았다'); burstAt(caretPoint(),true); shake(6); duel.i++;
 if(duel.i>=DUEL.length){ duel=null; $('duel').hidden=true; T.special=null; askCb=null; setMode(T.prevMode||'word',true); T.prevMode=null; S.camp.duelWon=true; S.objs.forEach(o=>{ if(o.t==='tower') o.calm=true; }); afterProgress(); return; }
 duelStep(); }

// ---------- modal helper ----------
function showModal(html,cb){ const w=$('modal2'); w.innerHTML=`<div class="modal">${html}</div>`; w.hidden=false; w.querySelectorAll('[data-m]').forEach(b=>b.onclick=()=>{ w.hidden=true; cb&&cb(b.dataset.m); refocus(); }); }

// ---------- campaign map screen ----------
let campSel=null;
function openCampaign(sel){ save(); started=false; closeDrawer(); closePop(); story&&endStory(); document.body.classList.add('titled'); $('title').hidden=true; const el=$('camp'); el.hidden=false;
 const unlocked=id=>{ const i=CAMPAIGN.findIndex(c=>c.id===id); return i===0||!!P.camp.done[CAMPAIGN[i-1].id]; };
 campSel=sel||campSel||(CAMPAIGN.find(c=>unlocked(c.id)&&!P.camp.done[c.id])||CAMPAIGN[CAMPAIGN.length-1]).id;
 const ch=chapterOf(campSel), has=hasSave(ch.id), stars=(P.camp.done[ch.id]||{}).stars||0, total=CAMPAIGN.reduce((a,c)=>a+((P.camp.done[c.id]||{}).stars||0),0);
 el.innerHTML=`<div class="cmap"><div class="cimg">${SPRITE_DATA.worldmap?`<img src="${SPRITE_DATA.worldmap.d}" alt="말결 군도 지도">`:''}
  ${CAMPAIGN.map(c=>{ const u=unlocked(c.id), s=(P.camp.done[c.id]||{}).stars||0; return `<button class="node ${c.id===campSel?'sel':''} ${u?'':'lock'} ${s?'clear':''}" style="left:${c.pos[0]}%;top:${c.pos[1]}%" data-c="${c.id}" ${u?'':'disabled'}><span class="no">${u?c.no:PH.lock}</span><span class="nm">${c.title}</span>${s?`<span class="st">${[1,2,3].map(i=>`<i class="${i<=s?'on':''}">${PH.sparkle}</i>`).join('')}</span>`:''}</button>`; }).join('')}</div>
  <aside class="cside"><small>말결 군도 캠페인 · 별 ${total}/18</small><h2>${ch.no}장 ${ch.title}</h2><div class="csub">${ch.sub}</div><p>${ch.blurb}</p>
  <h3>목표</h3><ul>${ch.goals.map(g=>`<li>${g.text}</li>`).join('')}</ul><h3>별 세 개 조건</h3><ul><li>목표 모두 달성</li><li>평균 정확도 90% 이상</li><li>${ch.star3.text}</li></ul>
  <div class="cbtn">${has?`<button class="btn primary" data-a="cont">이어하기</button><button class="btn" data-a="new">처음부터</button>`:`<button class="btn primary" data-a="new">${stars?'다시 하기':'시작하기'}</button>`}</div>
  <div class="cbot"><button class="btn sm" data-a="free">자유 모드</button><button class="btn sm" data-a="title">타이틀</button></div></aside></div>`;
 el.querySelectorAll('[data-c]').forEach(b=>b.onclick=()=>{ campSel=b.dataset.c; AU.tone(700,'triangle',0.05,0.06); openCampaign(campSel); });
 el.querySelectorAll('[data-a]').forEach(b=>b.onclick=()=>{ const a=b.dataset.a; AU.init();
  if(a==='cont'){ const d=loadSave(ch.id); if(d){ S=d; enterWorld(); } }
  else if(a==='new'){ if(has&&!b.dataset.arm){ b.dataset.arm='1'; b.textContent='진행 지우고 새로 시작'; return; } wipeSave(ch.id); S=newState(ch.id); enterWorld(); }
  else if(a==='free'){ const d=loadSave('free'); S=d||newState('free'); enterWorld(); }
  else if(a==='title'){ el.hidden=true; showTitle(); } }); }
function enterWorld(){ $('camp').hidden=true; P.last=S.map; saveProfile(); boot(); startGame(); const ch=curChapter();
 if(ch&&!S.camp.introSeen){ S.camp.introSeen=true; setTimeout(()=>playScript(ch.intro),700); } }
