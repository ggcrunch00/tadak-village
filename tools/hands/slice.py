# 생성한 왼손 PNG(투명 배경)를 손바닥(엄지 포함) + 손가락 4개로 자르고, 오른손은 좌우로 뒤집어 만든다.
# 출력: hands.json  {H, W, parts:{L:{palm:{img,x,y}, f:[{img,x,y,bx,by,tx,ty}...]}, R:{...}}}  (img는 webp data URI)
import sys, json, base64, io
import numpy as np
from PIL import Image
from collections import deque
class ndimage:
    @staticmethod
    def label(B):
        L=np.zeros(B.shape,int); n=0; H,W=B.shape
        for y in range(H):
            for x in range(W):
                if B[y,x] and not L[y,x]:
                    n+=1; L[y,x]=n; q=deque([(y,x)])
                    while q:
                        cy,cx=q.popleft()
                        for ny,nx in ((cy+1,cx),(cy-1,cx),(cy,cx+1),(cy,cx-1)):
                            if 0<=ny<H and 0<=nx<W and B[ny,nx] and not L[ny,nx]: L[ny,nx]=n; q.append((ny,nx))
        return L,n

src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGBA')
a = np.array(im)[:, :, 3]
ys, xs = np.where(a > 30)
im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
H0 = 460  # 기준 높이
im = im.resize((round(im.width * H0 / im.height), H0), Image.LANCZOS)
A = np.array(im)[:, :, 3] > 40
Hh, Ww = A.shape

def runs(row):
    r, s = [], None
    for x, v in enumerate(row):
        if v and s is None: s = x
        if not v and s is not None: r.append((s, x)); s = None
    if s is not None: r.append((s, len(row)))
    return r

# 손가락이 서로 떨어져 있는 가장 아래 줄(손가락 뿌리선) 찾기: 위에서부터 내려가며 왼쪽 4개 덩어리가 유지되는 마지막 줄
top = np.where(A.any(1))[0][0]
yk = None
for y in range(top, Hh):
    rs = [r for r in runs(A[y]) if r[1] - r[0] > 6]
    if len(rs) >= 4: yk = y
    elif yk is not None and y - yk > 3: break
assert yk, 'finger rows not found'
print('knuckle line', yk, 'of', Hh)
lab, n = ndimage.label(A[:yk + 1])
comps = []
for i in range(1, n + 1):
    yy, xx = np.where(lab == i)
    if len(yy) < 200: continue
    comps.append(dict(i=i, top=yy.min(), x0=xx.min(), x1=xx.max(), cx=xx.mean(), n=len(yy)))
comps.sort(key=lambda c: c['top'])
fingers = sorted(comps[:4], key=lambda c: c['cx'])  # 왼손: 왼쪽부터 새끼, 약지, 중지, 검지
print('fingers', [(c['x0'], c['x1'], c['top']) for c in fingers], 'others', [(c['x0'], c['x1'], c['top']) for c in comps[4:]])

rgba = np.array(im)
OVER = 22  # 손바닥과 겹치는 띠(이음새 감춤)
palm = rgba.copy()
parts = []
for c in fingers:
    m = np.zeros_like(A)
    m[:yk + 1] = lab == c['i']
    # 손가락 뿌리 아래로 조금 더(손바닥 쪽) 같은 열 범위를 붙임
    rs = [r for r in runs(A[yk]) if r[1] - r[0] > 6]
    rr = min(rs, key=lambda r: abs((r[0] + r[1]) / 2 - c['cx']))
    m[yk + 1:yk + 1 + OVER, rr[0]:rr[1]] = A[yk + 1:yk + 1 + OVER, rr[0]:rr[1]]
    yy, xx = np.where(m)
    x0, x1, y0, y1 = xx.min(), xx.max() + 1, yy.min(), yy.max() + 1
    f = rgba.copy(); f[~m] = 0
    # 겹치는 띠는 아래로 갈수록 투명하게
    for k in range(OVER - 6, OVER):  # 끝 몇 줄만 살짝 흐리게(겹침 띠는 불투명하게 둬서 이음새가 비치지 않게)
        f[yk + 1 + k, :, 3] = (f[yk + 1 + k, :, 3].astype(float) * (OVER - k) / 7).astype(np.uint8)
    KEEP = 34  # 손등 쪽에 손가락 뿌리를 남겨 두어 손가락과 위아래로 겹치게(틈이 보이지 않게)
    cut = lab == c['i']; cut[yk + 1 - KEEP:] = False
    palm[:yk + 1][cut] = 0
    bx = (rr[0] + rr[1]) / 2; by = yk
    tyy = yy.min(); txx = xx[yy == tyy].mean()
    parts.append(dict(img=Image.fromarray(f[y0:y1, x0:x1]), x=int(x0), y=int(y0), bx=float(bx), by=float(by), tx=float(txx), ty=float(tyy), w=float(rr[1] - rr[0])))
pimg = Image.fromarray(palm)

def uri(img):
    b = io.BytesIO(); img.save(b, 'WEBP', quality=86, method=6); return 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()

def side(flip):
    def F(img): return img.transpose(Image.FLIP_LEFT_RIGHT) if flip else img
    def X(x, w=0): return (Ww - x - w) if flip else x
    fs = []
    for p in parts:
        fs.append(dict(img=uri(F(p['img'])), iw=p['img'].width, ih=p['img'].height, x=X(p['x'], p['img'].width), y=p['y'], bx=(Ww - p['bx']) if flip else p['bx'], by=p['by'], tx=(Ww - p['tx']) if flip else p['tx'], ty=p['ty'], w=p['w']))
    if flip: fs = fs  # 오른손도 [새끼, 약지, 중지, 검지] 순서 유지
    return dict(palm=dict(img=uri(F(pimg)), x=0, y=0), f=fs)

data = dict(W=Ww, H=Hh, yk=int(yk), L=side(False), R=side(True))
json.dump(data, open(out, 'w'))
pimg.save(out.replace('.json', '_palm.png'))
for i, p in enumerate(parts): p['img'].save(out.replace('.json', f'_f{i}.png'))
print('size KB', round(len(json.dumps(data)) / 1024))
