"""Builds index.html from src.html by inlining the icon map and the sprite data.
assets/ph.js        Phosphor fill icons (MIT) as a JS object
assets/sprites.json sliced webp sprites (tools/slice_sheet.py over assets/sheet_*.png)"""
import pathlib, json
root=pathlib.Path(__file__).parent
src=(root/'src.html').read_text(encoding='utf-8')
ph=(root/'assets'/'ph.js').read_text(encoding='utf-8')
spr=json.loads((root/'assets'/'sprites.json').read_text())
spr.update(json.loads((root/'assets'/'art2.json').read_text()))
spr.update(json.loads((root/'assets'/'art3.json').read_text()))
assert '/*__PH__*/' in src and '/*__SPRITES__*/' in src
out=src.replace('/*__PH__*/',ph).replace('/*__SPRITES__*/','const SPRITE_DATA='+json.dumps(spr)+';')
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
