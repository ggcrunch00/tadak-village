import sys, json, base64, io
import numpy as np
from PIL import Image, ImageFilter
from collections import deque
src, names_csv, out = sys.argv[1], sys.argv[2], sys.argv[3]
COLS=int(sys.argv[4]) if len(sys.argv)>4 else 4; ROWS=int(sys.argv[5]) if len(sys.argv)>5 else 4; MAXD=int(sys.argv[6]) if len(sys.argv)>6 else 360
names = names_csv.split(',')
im = Image.open(src).convert('RGBA'); im = im.crop((0,0,im.width//4*4,im.height//4*4)); W,H = im.size
A = np.array(im.getchannel('A'))
S = 4
small = A.reshape(H//S,S,W//S,S).max(axis=(1,3)) > 60
h,w = small.shape
lab = np.zeros((h,w),dtype=np.int32); comps=[]
for y in range(h):
    for x in range(w):
        if small[y,x] and not lab[y,x]:
            cid=len(comps)+1; q=deque([(y,x)]); lab[y,x]=cid; pts=[]
            while q:
                cy,cx=q.popleft(); pts.append((cy,cx))
                for dy,dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                    ny,nx=cy+dy,cx+dx
                    if 0<=ny<h and 0<=nx<w and small[ny,nx] and not lab[ny,nx]:
                        lab[ny,nx]=cid; q.append((ny,nx))
            ys=[p[0] for p in pts]; xs=[p[1] for p in pts]
            comps.append(dict(id=cid,n=len(pts),y0=min(ys),y1=max(ys),x0=min(xs),x1=max(xs),cy=sum(ys)/len(ys),cx=sum(xs)/len(xs)))
big=[c for c in comps if c['n']>=150]
cw,ch=w/COLS,h/ROWS
owner={}
for c in big:
    cell=int(c['cy']//ch)*COLS+int(c['cx']//cw)
    # if two big comps fall in same cell, keep both (merge)
    owner.setdefault(cell,[]).append(c['id'])
def bdist(a,b):
    dx=max(0,max(a['x0'],b['x0'])-min(a['x1'],b['x1'])); dy=max(0,max(a['y0'],b['y0'])-min(a['y1'],b['y1'])); return max(dx,dy)
bigby={c['id']:c for c in big}
for c in comps:
    if c['n']>=150: continue
    best=None;bd=1e9
    for b in big:
        d=bdist(c,b)
        if d<bd: bd=d;best=b
    if best and bd<=10:
        cell=[k for k,v in owner.items() if best['id'] in v][0]; owner[cell].append(c['id'])
res={}
for i,name in enumerate(names):
    if name=='-' or i not in owner: print('missing',name); continue
    ids=owner[i]; m=np.isin(lab,ids)
    mfull=np.kron(m,np.ones((S,S),dtype=bool))
    ys,xs=np.where(mfull); y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    crop=im.crop((x0,y0,x1,y1)); a=np.array(crop.getchannel('A')).astype(np.uint8)
    a[~mfull[y0:y1,x0:x1]]=0; a[a<60]=0
    am=Image.fromarray(a).filter(ImageFilter.MinFilter(3)); crop.putalpha(am)
    bb=am.getbbox(); crop=crop.crop(bb)
    s=min(1.0,MAXD/max(crop.size))
    if s<1: crop=crop.convert('RGBa').resize((max(1,round(crop.width*s)),max(1,round(crop.height*s))),Image.LANCZOS).convert('RGBA')
    buf=io.BytesIO(); crop.save(buf,'WEBP',quality=88,alpha_quality=95,method=6)
    res[name]={'w':crop.width,'h':crop.height,'d':'data:image/webp;base64,'+base64.b64encode(buf.getvalue()).decode()}
    crop.save(f'spr_{name}.png')
json.dump(res,open(out,'w'))
print({k:(v['w'],v['h']) for k,v in res.items()})
