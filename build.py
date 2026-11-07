"""Builds index.html from src.html by inlining the icon map and the sprite data.
assets/ph.js        Phosphor fill icons (MIT) as a JS object
assets/sprites.json sliced webp sprites (tools/slice_sheet.py over assets/sheet_*.png)"""
import pathlib, json
root=pathlib.Path(__file__).parent
# 학급 로그인 모듈을 먼저 빌드 (원본 classlogin.src.js 만 고쳐도 배포에 반영되게)
import subprocess, sys, shutil as _sh, re as _re, tempfile, os
subprocess.run([sys.executable, str(root/'class-login'/'build.py')], check=True)
src=(root/'src.html').read_text(encoding='utf-8')
ph=(root/'assets'/'ph.js').read_text(encoding='utf-8')
spr=json.loads((root/'assets'/'sprites.json').read_text())
spr.update(json.loads((root/'assets'/'art2.json').read_text()))
spr.update(json.loads((root/'assets'/'art3.json').read_text()))
spr.update(json.loads((root/'assets'/'art4.json').read_text()))  # crest, flag, blank stone fixes
spr.update(json.loads((root/'assets'/'art5.json').read_text()))  # portraits redrawn in the map sprite style
spr.update(json.loads((root/'assets'/'art6.json').read_text()))  # 7-8장: 되울이, 메아리 바위, 원고대, 갈매기, 8개 섬 지도
spr.update(json.loads((root/'assets'/'art7.json').read_text()))  # 원정 '잊힌 말의 동굴' 장면 6장 (Codex, 글자 없음)
assert '/*__PH__*/' in src and '/*__SPRITES__*/' in src
# 학급 서버 주소와 공개 키(anon/publishable). server.json 이 없으면 서버 기능은 꺼진 채로 빌드됨
srv_path=root/'server.json'
srv=json.loads(srv_path.read_text()) if srv_path.exists() else None
srv=srv if srv and srv.get('url') and srv.get('key') else None
out=src.replace('/*__PH__*/',ph).replace('/*__SPRITES__*/','const SPRITE_DATA='+json.dumps(spr)+';').replace('/*__SERVER__*/','const SERVER_CFG='+json.dumps(srv)+';')
# 공용 학급 로그인 모듈(class-login/classlogin.js)을 한 파일 안에 넣음
cl_path=root/'class-login'/'classlogin.js'
out=out.replace('/*__CLASSLOGIN__*/', cl_path.read_text(encoding='utf-8') if cl_path.exists() else '')
(root/'index.html').write_text(out,encoding='utf-8')
print('built', len(out)//1024, 'KB')

# standalone package for any static host (GitHub Pages, Netlify, itch.io HTML5)
import zipfile
dist=root/'dist'; dist.mkdir(exist_ok=True)
page=('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
      '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
      '<meta name="description" content="타자로 자원을 모아 섬마을을 짓고, 말결 군도의 이름을 되찾는 타자 연습 시티빌더">\n'
      '<meta name="theme-color" content="#5fb4d0">\n'
      '<style>[hidden]{display:none!important}body{margin:0}</style>\n</head>\n<body>\n'+out+'\n</body>\n</html>\n')
(dist/'index.html').write_text(page,encoding='utf-8')
with zipfile.ZipFile(dist/'tadak-village-web.zip','w',zipfile.ZIP_DEFLATED) as z: z.write(dist/'index.html','index.html')
print('dist ready', (dist/'index.html').stat().st_size//1024, 'KB')

# 학급 로그인 관리 사이트(class-login)를 임시로 이 게임 사이트의 /class-login/ 에 함께 배포
# (공용 저장소 ggcrunch00/class-login 이 생기면 그쪽으로 옮김)
import shutil
cl=root/'class-login'
if (cl/'classlogin.js').exists():
    out_dir=dist/'class-login'; out_dir.mkdir(exist_ok=True)
    for f in ('index.html','classlogin.js','privacy.html'): shutil.copy(cl/f, out_dir/f)
    if srv: (out_dir/'server.json').write_text(json.dumps({**srv,'games':[{'app':'island','title':'이름을 쓰는 섬','url':'https://ggcrunch00.github.io/tadak-village/'}]},ensure_ascii=False))
    print('class-login site copied')

# 문법 검사: 빌드한 페이지의 인라인 스크립트를 node --check 로 확인 (node 가 있을 때만). 문법 오류면 배포를 멈춤
def check_js(html, label):
    if not _sh.which('node'): print('node 없음, 문법 검사 건너뜀'); return
    for k, js in enumerate(_re.findall(r'<script>(.*?)</script>', html, _re.S)):
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f: f.write(js); fn = f.name
        r = subprocess.run(['node', '--check', fn], capture_output=True, text=True); os.unlink(fn)
        if r.returncode: print(r.stderr[:2000]); raise SystemExit(f'{label} 스크립트 {k} 문법 오류')
    print(label, '문법 검사 통과')
check_js(out, 'game')
check_js((root/'class-login'/'index.html').read_text(encoding='utf-8'), 'class-login')
