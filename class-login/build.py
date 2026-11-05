"""classlogin.src.js + 그림(assets/icons.json) → classlogin.js (게임과 관리 사이트가 쓰는 파일)"""
import json, pathlib
root = pathlib.Path(__file__).parent
icons = json.loads((root / 'assets' / 'icons.json').read_text())
icons = {k: (v if isinstance(v, str) else v['d']) for k, v in icons.items()}
src = (root / 'classlogin.src.js').read_text(encoding='utf-8')
assert '/*__ICONS__*/{}' in src
(root / 'classlogin.js').write_text(src.replace('/*__ICONS__*/{}', json.dumps(icons)), encoding='utf-8')
print('classlogin.js', (root / 'classlogin.js').stat().st_size // 1024, 'KB')
