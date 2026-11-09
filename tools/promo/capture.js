// 홍보영상용 장면 캡처: 화면 UI를 숨긴 섬, 1920x1080 @2x
const { chromium } = require('playwright');
const fs = require('fs');
const OUT = __dirname + '/island/assets/';
const HIDE = `#fx,#hud,#res,#rail,#zoomCtl,#objTrack,#toasts,#levelWrap,#dock,.dock,#banner,#pop,#grade,#story,#drawer,#modal2,.objtrack,.zoomctl{display:none!important}`;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + __dirname + '/../page.html'); await p.waitForTimeout(1500);
  // 1) 타이틀 배경 (글자 없이 바다와 섬)
  await p.addStyleTag({ content: '.t-inner,.t-gear{visibility:hidden!important}' }); await p.waitForTimeout(800);
  await p.screenshot({ path: OUT + 'bg_title.png' });
  await p.addStyleTag({ content: '.t-inner,.t-gear{visibility:visible!important}' });
  await p.click('#btnLocal').catch(() => {}); await p.click('#whoAdd'); await p.fill('#whoName', 'promo'); await p.keyboard.press('Enter'); await p.waitForTimeout(300);
  await p.click('#btnFree'); await p.waitForTimeout(900); await p.click('#coachOk').catch(() => {});
  await p.addStyleTag({ content: HIDE });
  await p.evaluate(() => { const T = window.__tadak, S = T.S; S.castle = 3; Object.keys(S.res).forEach(k => S.res[k] = 99999); T.setClock(Math.floor(S.clock / 360) * 360 + 0.28 * 360); S.speed = 0; T.afterProgress(); });
  // 성 주변 자연물 정리
  await p.evaluate(() => { const T = window.__tadak, S = T.S; const c = S.objs.find(o => o.t === 'castle'); for (let k = S.objs.length - 1; k >= 0; k--) { const o = S.objs[k]; if (o.natural && o.t !== 'cave' && Math.abs(o.gx - c.gx) <= 7 && Math.abs(o.gy - c.gy) <= 7) S.objs.splice(k, 1); } T.afterProgress(); });
  // 카메라: 성 쪽으로 확대
  const cc = await p.evaluate(() => { const o = window.__tadak.S.objs.find(o => o.t === 'castle'); return window.__tadak.screenOf(o.gx + 1, o.gy + 2); });
  for (let i = 0; i < 4; i++) { await p.mouse.move(cc[0], cc[1]); await p.mouse.wheel(0, -300); await p.waitForTimeout(150); }
  await p.waitForTimeout(1200);
  // 2) 처음 섬 + 지을 자리 좌표
  const plan = await p.evaluate(() => { const T = window.__tadak, S = T.S; const c = S.objs.find(o => o.t === 'castle');
    const want = [['oak', -3, 3], ['well', 3, -1], ['bakery', -1, 3], ['cottage', 3, 2], ['windmill2', 5, 4]];
    const out = []; want.forEach(([n, dx, dy]) => { const x = c.gx + dx, y = c.gy + dy; const ok = T.canPlace(n === 'oak' ? 'flowers' : n === 'windmill2' ? 'windmill' : n, x, y) === true; const a = T.screenOf(x, y), bx = T.screenOf(x + 1, y); out.push({ n, x, y, ok, sx: a[0], sy: a[1], hw: bx[0] - a[0], hh: bx[1] - a[1] }); });
    return out; });
  fs.writeFileSync(OUT + 'plan.json', JSON.stringify(plan, null, 1)); console.log(JSON.stringify(plan));
  await p.screenshot({ path: OUT + 'island_early.png' });
  // 같은 카메라에서 다섯 건물을 실제로 지은 모습 (확인용)
  await p.evaluate(plan => { const T = window.__tadak, S = T.S; plan.forEach(q => { if (q.ok) S.objs.push({ t: q.n === 'oak' ? 'tree' : q.n === 'windmill2' ? 'windmill' : q.n, gx: q.x, gy: q.y, sz: 1, seed: 0 }); }); T.afterProgress(); }, plan);
  await p.waitForTimeout(800); await p.screenshot({ path: OUT + 'island_check.png' });
  // 3) 마을: 길과 건물 배치
  await p.evaluate(() => { const T = window.__tadak, S = T.S; const c = S.objs.find(o => o.t === 'castle'), gx = c.gx, gy = c.gy;
    const P = (x, y) => { const k = `${gx + x},${gy + y}`; if (T.isLand ? true : true) { if (!S.paths.includes(k) && !T.objAt(gx + x, gy + y)) S.paths.push(k); } };
    for (let x = -6; x <= 7; x++) P(x, 2); for (let y = -6; y <= 7; y++) P(2, y); for (let x = -3; x <= 4; x++) P(x, -1); for (let y = -1; y <= 2; y++) P(-1, y);
    const B = [['cottage', -4, 3], ['cottage', -5, 3], ['bakery', -2, 3], ['brickhouse', -3, 3], ['market', 0, 3], ['fountain', 1, 3], ['school', 3, 3], ['library', 4, 3], ['brickhouse', 5, 3], ['cottage', 6, 3],
      ['cottage', -4, 1], ['brickhouse', -3, 1], ['well', -2, 1], ['cottage', 3, 1], ['brickhouse', 4, 1], ['cottage', 5, 1], ['bakery', 6, 1],
      ['cottage', 3, -2], ['scriptorium', 4, -2], ['clocktower', 3, 0], ['lamp', 1, 1], ['lamp', -2, -2], ['lamp', 1, 4], ['flowers', 0, 4], ['flowers', -1, 4],
      ['cottage', 1, -2], ['brickhouse', 0, -2], ['cottage', -2, -2], ['kiln', 3, 5], ['lumber', -4, 5], ['windmill', 6, 5], ['windmill', -6, -3], ['watchtower', 7, 0], ['lighthouse', -7, 5], ['sakura', -1, 5], ['sakura', 1, 5], ['school', -4, -2]];
    B.forEach(([t, x, y], i) => { if (T.canPlace(t, gx + x, gy + y) === true) S.objs.push({ t, gx: gx + x, gy: gy + y, sz: 1, seed: i * 5 }); });
    S.stats.builtTotal = 60; T.afterProgress(); });
  await p.waitForTimeout(1500); await p.screenshot({ path: OUT + 'town_day.png' });
  await p.evaluate(() => { const T = window.__tadak; T.setClock(Math.floor(T.S.clock / 360) * 360 + 0.74 * 360); });
  await p.waitForTimeout(2000); await p.screenshot({ path: OUT + 'town_night.png' });
  // 4) 밤 침공
  await p.evaluate(() => window.__tadak.startRaid()); await p.waitForTimeout(17000);
  await p.evaluate(() => { const R = window.__tadak.raid; if (R) R.enemies.forEach((e, i) => { if (e.alive) e.t = 0.5 + (i % 4) * 0.07; }); });
  await p.waitForTimeout(400); await p.screenshot({ path: OUT + 'raid.png' });
  console.log('ships', await p.evaluate(() => (window.__tadak.raid || { enemies: [] }).enemies.filter(e => e.alive).map(e => e.word).join(',')));
  // 왼쪽 두 척을 고른 뒤, 그 배만 없앤 사진을 한 장 더
  const two = await p.evaluate(() => { const T = window.__tadak, R = T.raid; const al = R.enemies.filter(e => e.alive).map(e => ({ e, s: T.screenOf(e.x, e.y) })).sort((a, b) => a.s[0] - b.s[0]).slice(0, 2);
    const out = al.map(({ e, s }) => ({ word: e.word, x: s[0], y: s[1] })); al.forEach(({ e }) => { e.alive = false; e.dead = 1; }); return out; });
  await p.waitForTimeout(60); await p.screenshot({ path: OUT + 'raid_after.png' });
  fs.writeFileSync(OUT + 'raid.json', JSON.stringify(two)); console.log('two', JSON.stringify(two));
  console.log(errs.join('\n') || 'NO ERRORS'); await b.close();
})();
