from pathlib import Path
import re, struct
import numpy as np
from PIL import Image
from skoolkit.snapshot import Snapshot
root=Path(__file__).resolve().parents[1]
m=list(Snapshot.get(str(root/'assets/source/AticAtac.sna')).memory)
g=(root/'assets/source/AticAtac.GFX').read_bytes();rawpal=(root/'tools/spec256.raw.pal').read_bytes()
h=(root/'gen/assets.h').read_text();palvals=list(map(int,re.search(r'sprite_palette\[16\]=\{(.*?)\}',h)[1].split(',')))
pal=np.array([[(v&3)*85,((v>>2)&3)*85,((v>>4)&3)*85] for v in palvals])
def pic(typ):
 a=0xa600+(typ-1)*2;p=m[a]+256*m[a+1];w=m[p];ht=m[p+1];rgb=np.zeros((ht,w*8,3),dtype=np.uint8)
 for row in range(ht):
  for x in range(w*8):
   ad=p+2+row*w+x//8;c=g[(ad-0x4000)*8+7-(x%8)]
   if c not in (0,255):rgb[ht-1-row,x]=list(rawpal[c*3:c*3+3])
   elif c==255 and m[ad]&(128>>(x%8)):rgb[ht-1-row,x]=[255]*3
 return rgb
roast=pic(19);bones=pic(20)
print('Food dimensions',roast.shape,bones.shape)
assets=bytearray((root/'gen/assets.bin').read_bytes());bank=3+len(assets)//16384;data=bytearray();desc=[]
for level in range(31):
 rgb=np.zeros((32,48,3),dtype=np.uint8);rgb[32-len(bones):,:bones.shape[1]]=bones
 rows=min(len(roast),level)
 if rows:rgb[32-rows:,:roast.shape[1]]=roast[len(roast)-rows:]
 d=rgb.astype(np.int32)[...,None,:]-pal;idx=np.argmin(np.sum(d*d,axis=-1),axis=-1)
 tiles=bytearray()
 for yy in range(0,32,8):
  for xx in range(0,48,8):
   for y in range(8):
    for plane in range(4):
     v=0
     for x in range(8):v|=((int(idx[yy+y,xx+x])>>plane)&1)<<(7-x)
     tiles.append(v)
 if len(data)+len(tiles)>16384:assets.extend(data+bytes(16384-len(data)));bank+=1;data=bytearray()
 desc.append('{%d,0x%04x,768}'%(bank,0x8000+len(data)));data.extend(tiles)
assets.extend(data+bytes(16384-len(data)))
(root/'gen/assets.bin').write_bytes(assets)
(root/'gen/assets.h').write_text(h+'\nconst Blob food_blobs[31]={'+','.join(desc)+'};\n')
