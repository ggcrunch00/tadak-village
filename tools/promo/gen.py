"""30초 홍보영상: index.html(HyperFrames 구성) + audio.wav(오르골 반주와 효과음)를 한 시간표에서 만든다."""
import json, math, wave, struct
import numpy as np
from PIL import Image

D = '/tmp/claude-0/-home-user-tadak-village/cfdfcf47-f6b7-5751-ba83-be0ef360bdc4/scratchpad/promo/island/'
A = D + 'assets/'
plan = {q['n']: q for q in json.load(open(A + 'plan.json'))}
FIT = {'oak': (.92, .35), 'well': (.66, .6), 'bakery': (1.04, .92), 'cottage': (.98, .92), 'windmill2': (.6, .72)}

# ---------------- 시간표 ----------------
T_TITLE, T_TYPE, T_TOWN, T_NIGHT, T_RAID, T_CAVE, T_FRIENDS, T_END, END = 0, 3.6, 11.0, 13.4, 16.0, 19.6, 24.6, 27.2, 30.0
clicks, pops, whooshes, bursts, chimes = [], [], [], [], []

# ---------------- 한글 자모 단계 (타자 치는 모습) ----------------
CHO = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'
def stages(word):
    out, done = [], ''
    for ch in word:
        c = ord(ch) - 0xAC00
        if 0 <= c < 11172:
            L, V, Tt = c // 588, (c % 588) // 28, c % 28
            out.append(done + CHO[L]); out.append(done + chr(0xAC00 + (L * 21 + V) * 28))
            if Tt: out.append(done + ch)
        else:
            out.append(done + ch)
        done += ch
    return out

def esc(s): return s.replace('&', '&amp;').replace('<', '&lt;')

H = []   # 장면 HTML
TL = []  # GSAP 줄
def tl(s): TL.append(s)

# 타자 칸(게임 하단 칸과 같은 종이 카드) 하나: 단계별 글자를 겹쳐 두고 시간마다 하나씩 보이게
type_id = [0]
def typer(word, t0, dt, tag, x='50%', bottom=70, w=720, done_text='정확'):
    i = type_id[0]; type_id[0] += 1
    st = stages(word)
    spans = ''.join(f'<span class="ts" id="ts{i}_{k}">{esc(s)}<i class="caret"></i></span>' for k, s in enumerate(st))
    H.append(f'<div class="dock" id="dock{i}" style="left:{x};bottom:{bottom}px;width:{w}px"><div class="dtag">{tag}</div><div class="dtext"><span class="ts on0" id="ts{i}_e"><i class="caret"></i></span>{spans}</div><div class="seal" id="seal{i}">{done_text}</div></div>')
    tl(f'tl.set("#ts{i}_e",{{opacity:1}},{t0-0.5:.3f});')
    prev = f'#ts{i}_e'
    for k in range(len(st)):
        t = t0 + k * dt
        tl(f'tl.set("{prev}",{{opacity:0}},{t:.3f}); tl.set("#ts{i}_{k}",{{opacity:1}},{t:.3f});')
        prev = f'#ts{i}_{k}'; clicks.append(t)
    tend = t0 + len(st) * dt + 0.05
    tl(f'tl.fromTo("#seal{i}",{{opacity:0,scale:1.8,rotation:-14}},{{opacity:1,scale:1,rotation:-8,duration:.22,ease:"power3.out"}},{tend:.3f});')
    clicks.append(tend)
    return tend, i

# ---------------- 1. 타이틀 ----------------
logo1, logo2 = '이름을', '쓰는섬'
keys = ''.join(f'<span class="key" id="k{n}">{c}</span>' for n, c in enumerate(logo1))
keys2 = ''.join(f'<span class="key{" isle" if c=="섬" else ""}" id="k{n+3}">{c}</span>' for n, c in enumerate(logo2))
H.append(f'''<section class="clip scene" id="s1" data-start="0" data-duration="{T_TYPE+0.5}">
 <div class="bg" id="s1bg" style="background-image:url(assets/bg_title.png)"></div><div class="tint" style="background:linear-gradient(90deg,rgba(14,40,58,.7),rgba(14,40,58,.15) 62%,rgba(14,40,58,0))"></div>
 <div class="logo" id="logo"><div class="row">{keys}</div><div class="row r2">{keys2}</div><div class="sub" id="sub">말결 군도 이야기</div></div></section>''')
tl(f'tl.fromTo("#s1bg",{{scale:1.12}},{{scale:1.0,duration:{T_TYPE+0.5},ease:"power1.out"}},0);')
for n in range(6):
    t = 0.35 + n * 0.16
    tl(f'tl.fromTo("#k{n}",{{y:-60,opacity:0,scale:1.25}},{{y:0,opacity:1,scale:1,duration:.32,ease:"back.out(2.2)"}},{t:.3f});')
    tl(f'tl.to("#k{n}",{{y:6,duration:.07,yoyo:true,repeat:1,ease:"power1.inOut"}},{t+0.32:.3f});')
    clicks.append(t + 0.3)
tl('tl.fromTo("#sub",{opacity:0,y:16},{opacity:1,y:0,duration:.5,ease:"power2.out"},1.55);')
tl(f'tl.to("#s1",{{opacity:0,duration:.5,ease:"power1.in"}},{T_TYPE:.2f});'); whooshes.append(T_TYPE - 0.1)

# ---------------- 2~3. 글자를 치면 섬이 자라요 → 마을 → 밤 ----------------
sprites = ''
for n, q in plan.items():
    fw, fb = FIT[n]; hw, hh = q['hw'], q['hh']
    im = Image.open(A + n + '.png'); w = 2 * hw * fw; h = w * im.height / im.width; by = q['sy'] + hh * fb
    sprites += f'<div class="spr" id="sp_{n}" style="left:{q["sx"]-w/2:.1f}px;top:{by-h:.1f}px;width:{w:.1f}px;height:{h:.1f}px"><div class="sh" style="width:{w*0.9:.1f}px;left:{w*0.05:.1f}px"></div><img src="assets/{n}.png">'
    if n == 'windmill2':
        d = w * 1.4; sprites += f'<div class="sails" style="left:{w*0.31-d/2:.1f}px;top:{h*0.345-d/2:.1f}px;width:{d:.1f}px;height:{d:.1f}px"><img id="sails" src="assets/millsails.png"></div>'
    sprites += '</div>'
    for k in range(7):
        sprites += f'<i class="puff" id="pf_{n}_{k}" style="left:{q["sx"]:.1f}px;top:{by-6:.1f}px"></i>'
H.append(f'''<section class="clip scene" id="s2" data-start="{T_TYPE-0.5}" data-duration="{T_RAID-T_TYPE+1.0}">
 <div class="isl" id="isl"><div class="layer" style="background-image:url(assets/island_early.png)"></div>{sprites}
  <div class="layer" id="town" style="background-image:url(assets/town_day.png);opacity:0"></div>
  <div class="layer" id="night" style="background-image:url(assets/town_night.png);opacity:0"></div></div>
 <div class="vig"></div>
 <div class="cap" id="c2a"><b>글자를 치면</b></div><div class="cap c2" id="c2b"><b>섬이 자라요</b></div>
 <div class="cap" id="c3"><b>마을이 커지고</b></div><div class="cap" id="c3b"><b>밤이 오면 불이 켜져요</b></div></section>''')
tl(f'tl.fromTo("#s2",{{opacity:0}},{{opacity:1,duration:.5}},{T_TYPE-0.5:.2f});')
tl(f'tl.fromTo("#isl",{{scale:1.06}},{{scale:1.32,duration:{T_RAID-T_TYPE+1:.2f},ease:"none"}},{T_TYPE-0.5:.2f});')
tl(f'tl.fromTo("#c2a",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:.45,ease:"power3.out"}},{T_TYPE+0.2:.2f});')
tl(f'tl.fromTo("#c2b",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:.45,ease:"power3.out"}},{T_TYPE+0.6:.2f});')
words = [('나무', 'oak', '+ 나무'), ('우물', 'well', '+ 돌'), ('빵집', 'bakery', '+ 벽돌'), ('오두막', 'cottage', '+ 주민'), ('풍차', 'windmill2', '+ 나무')]
t = T_TYPE + 0.7
for word, n, gain in words:
    tend, i = typer(word, t, 0.085, '단어')
    pt = tend + 0.02
    tl(f'tl.fromTo("#sp_{n}",{{opacity:0,scale:.2,y:20}},{{opacity:1,scale:1,y:0,duration:.5,ease:"back.out(2.4)"}},{pt:.3f});'); pops.append(pt)
    for k in range(7):
        ang = k / 7 * math.tau; dx, dy = math.cos(ang) * 46, math.sin(ang) * 18
        tl(f'tl.fromTo("#pf_{n}_{k}",{{opacity:.9,scale:.4,x:0,y:0}},{{opacity:0,scale:1.6,x:{dx:.1f},y:{dy-8:.1f},duration:.6,ease:"power2.out"}},{pt:.3f});')
    tl(f'tl.set("#dock{i}",{{opacity:1}},{t-0.5:.3f}); tl.to("#dock{i}",{{opacity:0,duration:.15}},{pt+0.55:.3f});')
    t = pt + 0.62
tl(f'tl.to("#sails",{{rotation:540,duration:{T_RAID-T_TYPE:.2f},ease:"none"}},{T_TYPE:.2f});')
tl(f'tl.to(["#c2a","#c2b"],{{opacity:0,duration:.3}},{T_TOWN-0.3:.2f});')
tl(f'tl.to("#town",{{opacity:1,duration:.9,ease:"power1.inOut"}},{T_TOWN-0.2:.2f}); tl.to(".spr",{{opacity:0,duration:.6}},{T_TOWN+0.3:.2f});'); whooshes.append(T_TOWN - 0.2)
tl(f'tl.fromTo("#c3",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:.45,ease:"power3.out"}},{T_TOWN+0.3:.2f}); tl.to("#c3",{{opacity:0,duration:.3}},{T_NIGHT-0.2:.2f});')
tl(f'tl.to("#night",{{opacity:1,duration:1.1,ease:"power1.inOut"}},{T_NIGHT-0.3:.2f});')
tl(f'tl.fromTo("#c3b",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:.45,ease:"power3.out"}},{T_NIGHT+0.3:.2f}); tl.to("#c3b",{{opacity:0,duration:.3}},{T_RAID-0.3:.2f});')
chimes.append(T_NIGHT + 0.2)
tl(f'tl.to("#s2",{{opacity:0,duration:.45}},{T_RAID-0.1:.2f});'); whooshes.append(T_RAID - 0.15)

# ---------------- 4. 밤 침공 ----------------
RS = json.load(open(A + 'raid.json'))
ox = sum(r['x'] for r in RS) / len(RS) / 19.2; oy = sum(r['y'] for r in RS) / len(RS) / 10.8
patches = ''.join(f'<div class="gone" id="gone{j+1}" style="left:{r["x"]-80:.1f}px;top:{r["y"]-165:.1f}px;background-position:{-(r["x"]-80):.1f}px {-(r["y"]-165):.1f}px"></div><i class="boom" id="boom{j+1}" style="left:{r["x"]:.1f}px;top:{r["y"]-22:.1f}px"></i>' for j, r in enumerate(RS))
H.append(f'''<section class="clip scene" id="s4" data-start="{T_RAID-0.3}" data-duration="{T_CAVE-T_RAID+0.8}">
 <div class="isl" id="raidw" style="transform-origin:{ox:.1f}% {oy:.1f}%"><div class="layer" style="background-image:url(assets/raid.png)"></div>{patches}</div>
 <div class="vig"></div><div class="cap red right" id="c4"><b>밤에는 단어로 섬을 지켜요</b></div></section>''')
tl(f'tl.fromTo("#s4",{{opacity:0}},{{opacity:1,duration:.4}},{T_RAID-0.3:.2f}); tl.fromTo("#raidw",{{scale:1.25}},{{scale:1.75,duration:{T_CAVE-T_RAID+0.8:.2f},ease:"power1.inOut"}},{T_RAID-0.3:.2f});')
tl(f'tl.fromTo("#c4",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:.45,ease:"power3.out"}},{T_RAID+0.2:.2f});')
for j, (word, t0) in enumerate([(RS[0]['word'], T_RAID + 0.6), (RS[1]['word'], T_RAID + 2.1)]):
    tend, i = typer(word, t0, 0.07, '<span style="color:#c4373c">밤 침공</span>', done_text='격퇴')
    tl(f'tl.set("#dock{i}",{{opacity:1}},{t0-0.4:.3f}); tl.to("#dock{i}",{{opacity:0,duration:.15}},{tend+0.55:.3f});')
    tl(f'tl.fromTo("#boom{j+1}",{{opacity:1,scale:.2}},{{opacity:0,scale:2.4,duration:.55,ease:"power2.out"}},{tend:.3f}); tl.to("#gone{j+1}",{{opacity:1,duration:.25}},{tend+0.08:.3f});'); bursts.append(tend)
tl(f'tl.to("#s4",{{opacity:0,duration:.45}},{T_CAVE-0.1:.2f});'); whooshes.append(T_CAVE - 0.15)

# ---------------- 5. 동굴 원정 ----------------
cave = [('exp_gate', T_CAVE - 0.3, 1.9), ('exp_lake', T_CAVE + 1.5, 1.8), ('exp_statue', T_CAVE + 3.2, 2.2)]
layers = ''.join(f'<div class="layer kb" id="cv{n}" style="background-image:url(assets/{img}.jpg);opacity:0"></div>' for n, (img, _, _) in enumerate(cave))
H.append(f'''<section class="clip scene" id="s5" data-start="{T_CAVE-0.3}" data-duration="{T_FRIENDS-T_CAVE+0.8}">{layers}<div class="vig"></div>
 <div class="cap" id="c5"><b>동굴 원정</b></div><div class="cap c2 small" id="c5b"><b>핍과 함께 다섯 개의 방으로</b></div>
 <div class="riddle" id="rid"><small>부엉이 석상의 수수께끼</small>파면 팔수록 커지는 것은?</div></section>''')
for n, (img, t0, dur) in enumerate(cave):
    tl(f'tl.fromTo("#cv{n}",{{scale:1.04}},{{scale:1.12,duration:{dur+0.6:.2f},ease:"none"}},{t0:.2f}); tl.fromTo("#cv{n}",{{opacity:0}},{{opacity:1,duration:.4}},{t0:.2f});')
    if n: whooshes.append(t0)
tl(f'tl.fromTo("#c5",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:.45,ease:"power3.out"}},{T_CAVE+0.2:.2f}); tl.fromTo("#c5b",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:.45,ease:"power3.out"}},{T_CAVE+0.5:.2f});')
tl(f'tl.to(["#c5","#c5b"],{{opacity:0,duration:.3}},{T_CAVE+3.0:.2f});')
tl(f'tl.fromTo("#rid",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.4,ease:"power2.out"}},{T_CAVE+3.4:.2f});')
tend, i = typer('구멍', T_CAVE + 4.0, 0.09, '수수께끼', done_text='정답')
tl(f'tl.set("#dock{i}",{{opacity:1}},{T_CAVE+3.5:.3f}); tl.to("#dock{i}",{{opacity:0,duration:.3}},{T_FRIENDS-0.2:.3f});'); chimes.append(tend + 0.05)
tl(f'tl.to("#s5",{{opacity:0,duration:.45}},{T_FRIENDS-0.1:.2f});'); whooshes.append(T_FRIENDS - 0.15)

# ---------------- 6. 친구들 ----------------
F = [('ara', '아라', '등대지기'), ('moru', '모루', '건축 장인'), ('pip', '핍', '잉크 도깨비'), ('doeul', '되울이', '메아리 정령'), ('barto', '바르토', '항해사')]
cards = ''.join(f'<div class="fr" id="fr{n}"><img src="assets/{k}.png"><b>{nm}</b><small>{rl}</small></div>' for n, (k, nm, rl) in enumerate(F))
H.append(f'''<section class="clip scene" id="s6" data-start="{T_FRIENDS-0.3}" data-duration="{T_END-T_FRIENDS+0.8}">
 <div class="layer" id="wm" style="background-image:url(assets/worldmap.webp);filter:saturate(.9) brightness(.62)"></div><div class="vig"></div>
 <div class="cap center" id="c6"><b>말결 군도의 친구들과 함께</b></div><div class="friends">{cards}</div></section>''')
tl(f'tl.fromTo("#s6",{{opacity:0}},{{opacity:1,duration:.4}},{T_FRIENDS-0.3:.2f}); tl.fromTo("#wm",{{scale:1.15}},{{scale:1.03,duration:3.2,ease:"power1.out"}},{T_FRIENDS-0.3:.2f});')
tl(f'tl.fromTo("#c6",{{opacity:0,y:-20}},{{opacity:1,y:0,duration:.45,ease:"power3.out"}},{T_FRIENDS+0.1:.2f});')
for n in range(len(F)):
    t0 = T_FRIENDS + 0.35 + n * 0.17
    tl(f'tl.fromTo("#fr{n}",{{opacity:0,y:80}},{{opacity:1,y:0,duration:.5,ease:"back.out(1.6)"}},{t0:.2f});'); pops.append(t0 + 0.05)
tl(f'tl.to("#s6",{{opacity:0,duration:.45}},{T_END-0.1:.2f});'); whooshes.append(T_END - 0.15)

# ---------------- 7. 끝 화면 ----------------
keysE = ''.join(f'<span class="key" id="e{n}">{c}</span>' for n, c in enumerate(logo1))
keysE2 = ''.join(f'<span class="key{" isle" if c=="섬" else ""}" id="e{n+3}">{c}</span>' for n, c in enumerate(logo2))
H.append(f'''<section class="clip scene" id="s7" data-start="{T_END-0.3}" data-duration="{END-T_END+0.3}">
 <div class="bg" id="s7bg" style="background-image:url(assets/bg_title.png);filter:blur(3px) brightness(.8)"></div><div class="tint" style="background:rgba(14,40,58,.35)"></div>
 <div class="endbox"><div class="logo big"><div class="row">{keysE}</div><div class="row r2">{keysE2}</div></div>
  <div class="tag" id="tagl">한 글자씩, 섬이 자라요</div><div class="meta" id="meta">초등학생을 위한 한글·영어 타자 연습 · 학급 로그인으로 어디서나 이어서</div><div class="url" id="url">ggcrunch00.github.io/tadak-village</div></div></section>''')
tl(f'tl.fromTo("#s7",{{opacity:0}},{{opacity:1,duration:.45}},{T_END-0.3:.2f}); tl.fromTo("#s7bg",{{scale:1.08}},{{scale:1.0,duration:3,ease:"power1.out"}},{T_END-0.3:.2f});')
for n in range(6):
    t0 = T_END + 0.05 + n * 0.08
    tl(f'tl.fromTo("#e{n}",{{y:-50,opacity:0,scale:1.2}},{{y:0,opacity:1,scale:1,duration:.3,ease:"back.out(2)"}},{t0:.3f});'); clicks.append(t0 + 0.28)
tl(f'tl.fromTo("#tagl",{{opacity:0,y:14}},{{opacity:1,y:0,duration:.5,ease:"power2.out"}},{T_END+0.75:.2f});')
tl(f'tl.fromTo("#meta",{{opacity:0}},{{opacity:1,duration:.5}},{T_END+1.15:.2f}); tl.fromTo("#url",{{opacity:0}},{{opacity:1,duration:.5}},{T_END+1.35:.2f});')
tl(f'tl.to("#s7",{{opacity:0,duration:.5}},{END-0.5:.2f});')
chimes.append(T_END + 0.7)

CSS = r'''
@font-face{font-family:Bagel;src:url(assets/BagelFatOne.ttf)}
@font-face{font-family:Plex;src:url(assets/PlexKR-Bold.ttf);font-weight:700}
@font-face{font-family:Plex;src:url(assets/PlexKR-Medium.ttf);font-weight:500}
@font-face{font-family:Coding;src:url(assets/NanumCoding-Bold.ttf)}
:root{--paper:#fbf6ea;--ink:#2d2925;--edge:rgba(45,41,37,.86);--accent:#eba416;--seal:#c4432f}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden;background:#0e2a3a}
#root{position:relative;width:1920px;height:1080px;overflow:hidden;font-family:Plex,sans-serif;color:var(--ink)}
.scene{position:absolute;inset:0;overflow:hidden}
.bg,.layer{position:absolute;inset:0;background-size:cover;background-position:center}
.tint{position:absolute;inset:0}
.vig{position:absolute;inset:0;pointer-events:none;background:radial-gradient(ellipse at 50% 45%,rgba(0,0,0,0) 55%,rgba(8,20,30,.45) 100%)}
.isl{position:absolute;inset:0;transform-origin:52% 52%}
.logo{position:absolute;left:150px;top:250px;font-family:Bagel;font-size:150px;line-height:1;color:var(--ink)}
.logo .row{display:flex;gap:.07em;margin-bottom:.14em}.logo .r2{margin-left:.5em}
.key{display:inline-grid;place-items:center;width:1.18em;height:1.18em;padding-bottom:.1em;background:var(--paper);border-radius:.17em;box-shadow:0 0 0 .045em var(--edge),0 .08em 0 .045em var(--edge),0 .35em .6em rgba(14,48,66,.32)}
.key.isle{background:var(--accent);color:#3a2700;width:1.3em}
.sub{font-family:Bagel;font-size:54px;color:var(--paper);text-shadow:0 3px 0 rgba(14,48,66,.7),0 0 24px rgba(14,48,66,.6);margin-top:10px;letter-spacing:.04em}
.spr{position:absolute;opacity:0;transform-origin:50% 100%}.spr img{position:absolute;left:0;top:0;width:100%;height:100%}
.spr .sh{position:absolute;bottom:-6px;height:16px;border-radius:50%;background:rgba(28,58,34,.28);filter:blur(3px)}
.sails{position:absolute;transform:scaleX(.82)}.sails img{width:100%;height:100%;display:block}
.puff{position:absolute;width:26px;height:26px;margin:-13px 0 0 -13px;border-radius:50%;background:rgba(255,250,235,.95);opacity:0}
.cap{position:absolute;left:110px;top:96px;font-family:Bagel;font-size:74px;line-height:1}
.cap b{display:inline-block;font-weight:400;background:var(--paper);padding:.18em .42em .26em;border-radius:.22em;box-shadow:0 0 0 3px var(--edge),0 6px 0 3px var(--edge),0 22px 40px rgba(10,30,45,.35)}
.cap.c2{top:208px}.cap.small{font-size:48px;top:200px}.cap.red b{color:#fff;background:#c4373c}
.cap.right{left:auto;right:110px}
.gone{position:absolute;width:160px;height:215px;background-image:url(assets/raid_after.png);background-size:1920px 1080px;opacity:0;-webkit-mask-image:radial-gradient(ellipse 50% 50% at 50% 50%,#000 70%,transparent 100%);mask-image:radial-gradient(ellipse 50% 50% at 50% 50%,#000 70%,transparent 100%)}
.cap.center{left:0;right:0;text-align:center;top:110px}
.dock{position:absolute;transform:translateX(-50%);height:150px;background:var(--paper);border-radius:22px;opacity:0;box-shadow:0 0 0 3px var(--edge),0 6px 0 3px var(--edge),0 26px 50px rgba(10,30,45,.4);padding:18px 34px}
.dtag{font-size:22px;font-weight:700;color:#5f574c}
.dtext{position:relative;height:84px;margin-top:4px;border-bottom:3px solid rgba(45,41,37,.16)}
.ts{position:absolute;left:0;bottom:6px;font-size:66px;font-weight:700;opacity:0;white-space:nowrap;display:flex;align-items:center}
.caret{display:inline-block;width:5px;height:62px;background:var(--accent);margin-left:6px;border-radius:3px}
.seal{position:absolute;right:30px;top:36px;font-family:Bagel;font-size:40px;color:var(--seal);border:5px solid var(--seal);border-radius:14px;padding:2px 14px 6px;opacity:0;transform:rotate(-8deg)}
.boom{position:absolute;width:150px;height:150px;margin:-75px 0 0 -75px;border-radius:50%;opacity:0;background:radial-gradient(circle,rgba(255,236,170,1) 0,rgba(255,200,90,.85) 35%,rgba(255,170,60,0) 70%)}
.riddle{position:absolute;left:50%;top:130px;transform:translateX(-50%);background:rgba(20,26,36,.82);color:#fff;font-size:54px;font-weight:700;padding:26px 48px 32px;border-radius:24px;opacity:0;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.4)}
.riddle small{display:block;font-size:26px;color:#ffd77a;font-weight:500;margin-bottom:8px}
.friends{position:absolute;left:0;right:0;bottom:120px;display:flex;justify-content:center;gap:44px}
.fr{width:260px;text-align:center;opacity:0}.fr img{width:250px;height:274px;object-fit:contain;filter:drop-shadow(0 18px 24px rgba(0,0,0,.45))}
.fr b{display:block;font-family:Bagel;font-weight:400;font-size:46px;color:var(--paper);text-shadow:0 3px 0 rgba(0,0,0,.4);margin-top:6px}.fr small{font-size:24px;color:#e8e0cf;font-weight:500}
.endbox{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.logo.big{position:relative;left:auto;top:auto;font-size:132px}
.tag{font-family:Bagel;font-size:68px;color:var(--paper);text-shadow:0 4px 0 rgba(14,48,66,.55);margin-top:26px}
.meta{font-size:32px;font-weight:500;color:#eaf3f6;margin-top:22px}
.url{font-family:Coding;font-size:30px;color:#ffd77a;margin-top:16px;letter-spacing:.02em}
'''
html = f'''<!doctype html>
<html lang="ko" data-resolution="landscape"><head><meta charset="UTF-8"><meta name="viewport" content="width=1920, height=1080">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script><style>{CSS}</style></head>
<body><div id="root" data-composition-id="main" data-start="0" data-duration="{END}" data-width="1920" data-height="1080">
{chr(10).join(H)}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(TL)}
window.__timelines["main"] = tl;
tl.seek(0);
</script></body></html>'''
open(D + 'index.html', 'w', encoding='utf-8').write(html)
json.dump({'clicks': clicks, 'pops': pops, 'whooshes': whooshes, 'bursts': bursts, 'chimes': chimes}, open(D + 'events.json', 'w'))

# ---------------- 소리 ----------------
SR = 48000; N = int(SR * END); L = np.zeros(N); R = np.zeros(N)
def add(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR); j = min(N, i + len(sig))
    if i >= N or j <= i: return
    s = sig[:j - i] * gain; L[i:j] += s * (1 - max(0, pan)); R[i:j] += s * (1 + min(0, pan))
def bell(f, dur=1.6, amp=0.22):
    t = np.arange(int(SR * dur)) / SR
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 3.2) + 0.35 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 5.5) + 0.12 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 8)
    s *= np.minimum(1, t / 0.004); return s * amp
def soft(f, dur, amp=0.07):
    t = np.arange(int(SR * dur)) / SR
    s = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2 * t)) * np.minimum(1, t / 0.08) * np.exp(-t * 1.1); return s * amp
def noise(dur, seed):
    rng = np.random.default_rng(seed); return rng.standard_normal(int(SR * dur))
def lp(x, a):
    y = np.empty_like(x); acc = 0.0
    for k in range(len(x)): acc += a * (x[k] - acc); y[k] = acc
    return y
NOTE = lambda n: 440 * 2 ** ((n - 69) / 12)
BPM = 96; beat = 60 / BPM
# 화음: C - G - Am - F, 한 마디 4박
prog = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]
mel = [76, 74, 72, 74, 76, 79, 76, 74, 72, 74, 76, 72, 74, 72, 69, 72,
       76, 74, 72, 74, 76, 79, 81, 79, 77, 76, 74, 72, 74, 76, 72, 0]
bar = 4 * beat; t0 = 0.2
nb = int((END - t0) / bar) + 1
for b in range(nb):
    ch = prog[b % 4]; tb = t0 + b * bar
    add(soft(NOTE(ch[0] - 12), bar * 1.1, 0.10), tb)
    for k, n in enumerate(ch): add(soft(NOTE(n), bar * 1.05, 0.035), tb + 0.01 * k, pan=(k - 1) * 0.3)
    for s in range(8):  # 8분음표 오르골
        idx = (b * 8 + s) % len(mel); n = mel[idx]
        if n and (s % 2 == 0 or b % 2 == 1):
            add(bell(NOTE(n), 1.4, 0.16), tb + s * beat / 2, pan=0.15 * math.sin(idx))
# 효과음
for k, t in enumerate(clicks):
    s = noise(0.03, k) ; s = np.diff(np.concatenate([[0], s])) * np.exp(-np.arange(len(s)) / SR * 160) * 0.22
    s += np.sin(2 * np.pi * 1900 * np.arange(len(s)) / SR) * np.exp(-np.arange(len(s)) / SR * 220) * 0.08
    add(s, t, pan=((k * 37) % 7 - 3) * 0.05)
for k, t in enumerate(pops):
    n = int(SR * 0.16); tt = np.arange(n) / SR; f = 380 + 900 * tt / 0.16
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 18) * 0.28; add(s, t); add(bell(NOTE(84 + (k % 3) * 3), 0.9, 0.12), t + 0.05)
for k, t in enumerate(whooshes):
    n = int(SR * 0.55); tt = np.arange(n) / SR; env = np.sin(np.pi * tt / 0.55) ** 2
    s = lp(noise(0.55, 100 + k), 0.06) * env * 0.5; add(s, t - 0.25)
for k, t in enumerate(bursts):
    n = int(SR * 0.5); tt = np.arange(n) / SR
    s = lp(noise(0.5, 200 + k), 0.12) * np.exp(-tt * 9) * 0.6 + np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 12) * 0.5
    add(s, t); add(bell(NOTE(88), 0.8, 0.1), t + 0.06)
for k, t in enumerate(chimes):
    for j, n in enumerate([72, 76, 79, 84]): add(bell(NOTE(n), 1.6, 0.14), t + j * 0.07, pan=(j - 1.5) * 0.2)
# 끝 화음과 페이드
for n in [48, 60, 64, 67, 72]: add(soft(NOTE(n), 3.2, 0.09), T_END + 0.1)
fade = np.ones(N); fi = int(SR * 0.4); fo = int(SR * 1.6); fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
L *= fade; R *= fade
pk = max(np.abs(L).max(), np.abs(R).max()); L *= 0.89 / pk; R *= 0.89 / pk
data = (np.stack([L, R], 1) * 32767).astype('<i2').tobytes()
with wave.open(D + 'assets/audio.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data)
print('ok', len(clicks), 'clicks', len(pops), 'pops')
