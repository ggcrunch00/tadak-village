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
# 손은 자르지 않고 원본 그대로 쓴다(이음새 없음). 손가락마다 '강조용' 조각만 만든다:
# 손가락 부분 + 손등 쪽으로 FADE 줄 동안 점점 투명해지는 꼬리(색이 손등으로 자연스럽게 스며들게)
FADE = 30
parts = []
for c in fingers:
    m = np.zeros(A.shape, float)
    m[:yk + 1][lab == c['i']] = 1
    rs = [r for r in runs(A[yk]) if r[1] - r[0] > 6]
    rr = min(rs, key=lambda r: abs((r[0] + r[1]) / 2 - c['cx']))
    for k in range(FADE):
        y = yk + 1 + k
        if y >= Hh: break
        m[y, rr[0]:rr[1]] = A[y, rr[0]:rr[1]] * (1 - (k + 1) / FADE) ** 1.5
    # 손가락 뿌리 쪽도 미리 조금씩 옅게(색 경계가 딱 끊기지 않게)
    for k in range(12):
        y = yk - k
        m[y][lab[y] == c['i']] *= 0.55 + 0.45 * k / 12
    yy, xx = np.where(m > 0)
    x0, x1, y0, y1 = xx.min(), xx.max() + 1, yy.min(), yy.max() + 1
    f = rgba.copy().astype(float); f[:, :, 3] *= m; f = f.astype(np.uint8)
    tyy = yy.min(); txx = xx[yy == tyy].mean()
    parts.append(dict(img=Image.fromarray(f[y0:y1, x0:x1]), x=int(x0), y=int(y0), tx=float(txx), ty=float(tyy)))
himg = Image.fromarray(rgba)

def uri(img):
    b = io.BytesIO(); img.save(b, 'WEBP', quality=86, method=6); return 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()

def side(flip):
    def F(img): return img.transpose(Image.FLIP_LEFT_RIGHT) if flip else img
    fs = [dict(img=uri(F(p['img'])), iw=p['img'].width, ih=p['img'].height, x=(Ww - p['x'] - p['img'].width) if flip else p['x'], y=p['y'], tx=(Ww - p['tx']) if flip else p['tx'], ty=p['ty']) for p in parts]
    return dict(hand=uri(F(himg)), f=fs)  # 손가락 순서: [새끼, 약지, 중지, 검지]

data = dict(W=Ww, H=Hh, yk=int(yk), L=side(False), R=side(True))
json.dump(data, open(out, 'w'))
for i, p in enumerate(parts): p['img'].save(out.replace('.json', f'_f{i}.png'))
print('size KB', round(len(json.dumps(data)) / 1024))
