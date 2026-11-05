"""Turn a flat-magenta background (Codex images are RGB) into alpha."""
import sys, numpy as np
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
a = np.array(Image.open(src).convert('RGB')).astype(np.int32)
r,g,b = a[...,0],a[...,1],a[...,2]
mag = (np.minimum(r,b) - g)             # how magenta a pixel is
alpha = np.clip(255 - (mag-60)*255/80, 0, 255)   # >=140 fully transparent, <=60 opaque
alpha[(mag<60)] = 255
# despill: pull magenta tint out of semi-transparent edge pixels
edge = (alpha<255)&(alpha>0)
k = np.clip(mag-20,0,None)
r2 = np.where(edge, np.clip(r-k*0.8,0,255), r); b2 = np.where(edge, np.clip(b-k*0.8,0,255), b)
out = np.dstack([r2,g,b2,alpha]).astype(np.uint8)
Image.fromarray(out,'RGBA').save(dst)
