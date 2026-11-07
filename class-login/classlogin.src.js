/* class-login: 학급 로그인 공용 모듈 (여러 게임이 같이 씀)
 * 학생: 학급 코드(5글자) + 번호 + 그림 비밀번호(동물 1 + 과일 1). 이름은 다루지 않음.
 * 선생님: Google 로그인 (관리 사이트에서 사용).
 * 서버: Supabase (supabase/schema.sql). 라이브러리 없이 fetch 만 씀.
 *
 * 사용 (게임 쪽):
 *   ClassLogin.init({url, key, app:'island'})
 *   ClassLogin.mountStudentLogin(el, {onLogin(session){...}})
 *   ClassLogin.load() / ClassLogin.save(part, data) / ClassLogin.logout()
 */
(function (root) {
  'use strict';
  const ANIMALS = ['고양이', '강아지', '토끼', '곰', '펭귄', '거북이', '여우', '부엉이'];
  const FRUITS = ['사과', '바나나', '포도', '딸기', '수박', '복숭아', '귤', '파인애플'];
  const ICONS = /*__ICONS__*/{};
  const SKEY = 'class-login-session';
  let CFG = null;

  function cfg() { if (!CFG || !CFG.url || !CFG.key) throw { code: 'no_server' }; return CFG; }
  async function req(path, { method = 'GET', body, token, prefer, keepalive } = {}) {
    const c = cfg(); const h = { apikey: c.key, 'Content-Type': 'application/json' };
    // 새 공개 키(sb_publishable_...)는 JWT 가 아니라서 apikey 헤더에만 넣어요. Bearer 에는 로그인한 선생님 토큰만.
    // 예전 anon 키(JWT)는 Bearer 에 넣어도 되지만, 넣지 않아도 anon 으로 처리돼요.
    if (token) h.Authorization = 'Bearer ' + token;
    if (prefer) h.Prefer = prefer;
    const bs = body === undefined ? undefined : JSON.stringify(body);
    // 창을 닫을 때(pagehide) 보내는 저장은 keepalive 로 끝까지 가게 함. 브라우저 한도(64KB) 안일 때만
    let r; try { r = await fetch(c.url.replace(/\/+$/, '') + path, { method, headers: h, body: bs, keepalive: !!keepalive && !!bs && bs.length < 60000 }); }
    catch (e) { throw { code: 'offline' }; }
    const txt = await r.text(); let j = null; try { j = txt ? JSON.parse(txt) : null; } catch (e) { }
    if (!r.ok) throw { code: r.status === 401 ? 'auth' : 'http', status: r.status, msg: (j && (j.msg || j.message || j.error_description || j.error)) || txt };
    return j;
  }
  const rpc = (fn, args, token, opt = {}) => req('/rest/v1/rpc/' + fn, { method: 'POST', body: args, token, keepalive: opt.keepalive });

  // ---------- 학생 ----------
  function session() { try { return JSON.parse(sessionStorage.getItem(SKEY) || 'null'); } catch (e) { return null; } }
  function setSession(s) { if (s) sessionStorage.setItem(SKEY, JSON.stringify(s)); else sessionStorage.removeItem(SKEY); }
  async function login(code, num, secret) {
    const r = await rpc('cl_student_login', { p_code: toCode(code), p_num: +num, p_secret: secret });
    if (r && r.ok) setSession({ token: r.token, student: r.student, cls: r.class });
    return r;
  }
  async function load() { const s = session(); if (!s) throw { code: 'no_session' }; return rpc('cl_student_load', { p_token: s.token, p_app: cfg().app }); }
  async function save(part, data, opt = {}) { const s = session(); if (!s) throw { code: 'no_session' }; return rpc('cl_student_save', { p_token: s.token, p_app: cfg().app, p_part: part, p_data: data }, undefined, opt); }
  async function logout() { const s = session(); setSession(null); if (s) { try { await rpc('cl_student_logout', { p_token: s.token }); } catch (e) { } } }
  // 한글 자판 상태로 학급 코드를 쳐도 두벌식 자리대로 영문으로 바꿈 (ㅏ→K, 가→RK). 대소문자 구분 없음
  const CHO = 'rRseEfaqQtTdwWczxvg', JUNG = ['k','o','i','O','j','p','u','P','h','hk','ho','hl','y','n','nj','np','nl','b','m','ml','l'],
    JONG = ['','r','R','rt','s','sw','sg','e','f','fr','fa','fq','ft','fx','fv','fg','a','q','qt','t','T','d','w','c','z','x','v','g'];
  const COMPAT = {}; 'ㄱㄲㄳㄴㄵㄶㄷㄸㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅃㅄㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'.split('').forEach((c, i) => COMPAT[c] = ['r','R','rt','s','sw','sg','e','E','f','fr','fa','fq','ft','fx','fv','fg','a','q','Q','qt','t','T','d','w','W','c','z','x','v','g'][i]);
  'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'.split('').forEach((c, i) => COMPAT[c] = JUNG[i]);
  function toCode(str) { let out = ''; for (const ch of String(str || '')) { const c = ch.charCodeAt(0);
      if (c >= 0xAC00 && c <= 0xD7A3) { const k = c - 0xAC00, cho = Math.floor(k / 588), jung = Math.floor((k % 588) / 28), jong = k % 28; out += CHO[cho] + JUNG[jung] + JONG[jong]; }
      else if (COMPAT[ch]) out += COMPAT[ch]; else out += ch; }
    return out.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 8); }
  const secretOf = (a, f) => 'a' + a + '-f' + f;
  const parseSecret = s => { const m = /^a([0-7])-f([0-7])$/.exec(s || ''); return m ? [+m[1], +m[2]] : null; };
  const icon = (kind, i) => ICONS[kind + i] ? `<img src="${ICONS[kind + i]}" alt="${(kind === 'a' ? ANIMALS : FRUITS)[i]}">` : `<span class="clx-txt">${(kind === 'a' ? ANIMALS : FRUITS)[i]}</span>`;

  const ERR = { no_class: '그런 학급 코드가 없어요. 다시 확인해요.', no_student: '그 번호는 이 학급에 없어요. 선생님께 물어봐요.', bad_secret: '그림 비밀번호가 달라요.', locked: '여러 번 틀려서 5분 동안 잠겼어요. 잠시 뒤에 해요.', offline: '서버에 연결할 수 없어요. 인터넷을 확인해요.' };
  function mountStudentLogin(el, { onLogin, onCancel } = {}) {
    let pick = { a: null, f: null };
    el.innerHTML = `<form class="clx" autocomplete="off">
      <div class="clx-row"><label>학급 코드<input name="code" maxlength="12" placeholder="예: K7M2Q" autocapitalize="characters" autocomplete="off" spellcheck="false" lang="en" style="text-transform:uppercase"></label>
      <label>번호<input name="num" inputmode="numeric" maxlength="2" placeholder="12"></label></div>
      <div class="clx-h">그림 비밀번호: 동물 하나, 과일 하나를 눌러요</div>
      <div class="clx-grid" data-k="a">${ANIMALS.map((n, i) => `<button type="button" data-i="${i}" aria-label="${n}">${icon('a', i)}</button>`).join('')}</div>
      <div class="clx-grid" data-k="f">${FRUITS.map((n, i) => `<button type="button" data-i="${i}" aria-label="${n}">${icon('f', i)}</button>`).join('')}</div>
      <div class="clx-foot"><span class="clx-msg"></span><span>${onCancel ? '<button type="button" class="clx-cancel">취소</button>' : ''}<button type="submit" class="clx-go">로그인</button></span></div></form>`;
    const f = el.querySelector('form'), msg = el.querySelector('.clx-msg');
    // 조합 중에는 건드리지 않고, 조합이 끝나거나 영문으로 쳤을 때 바로 대문자 코드로 바꿈
    const fix = () => { const v = toCode(f.code.value); if (v !== f.code.value) f.code.value = v; };
    f.code.addEventListener('compositionend', () => setTimeout(fix, 0)); f.code.addEventListener('input', e => { if (!e.isComposing) fix(); }); f.code.addEventListener('blur', fix);
    el.querySelectorAll('.clx-grid').forEach(g => g.querySelectorAll('button').forEach(b => b.onclick = () => {
      pick[g.dataset.k] = +b.dataset.i; g.querySelectorAll('button').forEach(x => x.classList.toggle('on', x === b)); }));
    const cc = el.querySelector('.clx-cancel'); if (cc) cc.onclick = () => onCancel();
    f.onsubmit = async e => { e.preventDefault(); fix(); const code = toCode(f.code.value), num = parseInt(f.num.value, 10);
      if (code.length < 4 || !num) { msg.textContent = '학급 코드와 번호를 넣어요.'; return; }
      if (pick.a === null || pick.f === null) { msg.textContent = '동물 하나와 과일 하나를 골라요.'; return; }
      msg.textContent = '확인하는 중...';
      try { const r = await login(code, num, secretOf(pick.a, pick.f));
        if (r && r.ok) { msg.textContent = ''; onLogin && onLogin(session()); }
        else msg.textContent = ERR[r && r.error] || '로그인하지 못했어요.'; }
      catch (err) { msg.textContent = ERR[err.code] || ('로그인하지 못했어요 (' + (err.status || err.code) + ')'); } };
  }
  const CSS = `.clx{display:flex;flex-direction:column;gap:8px}.clx-row{display:flex;gap:8px;flex-wrap:wrap}.clx label{display:flex;flex-direction:column;gap:3px;font-size:12px;font-weight:600;color:#5f574c}
.clx input{font:inherit;font-size:16px;border:0;background:#f0e7d4;border-radius:10px;padding:8px 10px;width:120px;letter-spacing:.08em}.clx input[name=num]{width:70px}
.clx-h{font-size:12.5px;font-weight:600;color:#5f574c;margin-top:2px}.clx-grid{display:grid;grid-template-columns:repeat(8,1fr);gap:5px}
.clx-grid button{appearance:none;border:0;background:#f0e7d4;border-radius:10px;padding:4px;cursor:pointer;height:clamp(44px,5.2vw,58px);display:grid;place-items:center;min-width:0;overflow:hidden}
.clx-grid button img{max-width:100%;max-height:100%;object-fit:contain;display:block}.clx-grid button.on{background:#fbe7b8;box-shadow:0 0 0 2px #2d2925}
.clx-txt{font-size:11px}.clx-foot{display:flex;justify-content:space-between;align-items:center;gap:8px}.clx-msg{font-size:12.5px;color:#5f574c}
.clx-go,.clx-cancel{appearance:none;border:0;border-radius:9px;padding:8px 16px;font:inherit;font-weight:600;cursor:pointer;background:#eba416;color:#3a2700;box-shadow:0 0 0 1.5px #2d2925,0 2px 0 1.5px #2d2925;margin-left:6px}.clx-cancel{background:#f0e7d4;box-shadow:inset 0 0 0 1px rgba(45,41,37,.14)}
@media (max-width:520px){.clx-grid{grid-template-columns:repeat(4,1fr)}}`;
  function injectCSS() { if (document.getElementById('clx-css')) return; const s = document.createElement('style'); s.id = 'clx-css'; s.textContent = CSS; document.head.appendChild(s); }

  // ---------- 선생님 (Google 로그인) ----------
  const TKEY = 'class-login-teacher';
  function tsess() { try { return JSON.parse(localStorage.getItem(TKEY) || 'null'); } catch (e) { return null; } }
  function setT(j) { if (!j) { localStorage.removeItem(TKEY); return null; } const o = { access_token: j.access_token, refresh_token: j.refresh_token, expires_at: Date.now() + ((+j.expires_in || 3600) - 60) * 1000, email: j.email || (tsess() || {}).email || '' }; localStorage.setItem(TKEY, JSON.stringify(o)); return o; }
  function googleSignIn(redirectTo) { const c = cfg(); location.href = c.url.replace(/\/+$/, '') + '/auth/v1/authorize?provider=google&redirect_to=' + encodeURIComponent(redirectTo || location.href.split('#')[0]); }
  async function handleRedirect() { // Supabase 가 #access_token=... 으로 돌려보냄
    if (!location.hash.includes('access_token=')) return tsess();
    const p = new URLSearchParams(location.hash.slice(1)); const j = { access_token: p.get('access_token'), refresh_token: p.get('refresh_token'), expires_in: p.get('expires_in') };
    history.replaceState(null, '', location.href.split('#')[0]);
    try { const u = await req('/auth/v1/user', { token: j.access_token }); j.email = u && u.email; } catch (e) { }
    return setT(j);
  }
  async function ttoken() { let t = tsess(); if (!t) throw { code: 'auth' };
    if (Date.now() > t.expires_at) { try { t = setT(await req('/auth/v1/token?grant_type=refresh_token', { method: 'POST', body: { refresh_token: t.refresh_token } })); } catch (e) { setT(null); throw { code: 'auth' }; } }
    return t.access_token; }
  const teacher = {
    session: tsess, signIn: googleSignIn, handleRedirect, signOut() { setT(null); },
    async get(path) { return req(path, { token: await ttoken() }); },
    async post(path, body, prefer) { return req(path, { method: 'POST', body, prefer, token: await ttoken() }); },
    async patch(path, body) { return req(path, { method: 'PATCH', body, token: await ttoken() }); },
    async del(path) { return req(path, { method: 'DELETE', token: await ttoken() }); },
    async rpc(fn, args) { return rpc(fn, args, await ttoken()); }
  };

  root.ClassLogin = {
    ANIMALS, FRUITS, ICONS, init(c) { CFG = c; injectCSS(); return this; }, on() { return !!(CFG && CFG.url && CFG.key); },
    login, load, save, logout, session, secretOf, toCode, parseSecret, icon, mountStudentLogin, teacher, req
  };
})(typeof window !== 'undefined' ? window : this);
