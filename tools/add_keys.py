from pathlib import Path
import re, numpy as np
from skoolkit.snapshot import Snapshot
root=Path(__file__).resolve().parents[1]
m=list(Snapshot.get(str(root/'assets/source/AticAtac.sna')).memory)
h=(root/'gen/assets.h').read_text();pv=list(map(int,re.search(r'sprite_palette\[16\]=\{(.*?)\}',h)[1].split(',')));pal=np.array([[(v&3)*85,((v>>2)&3)*85,((v>>4)&3)*85] for v in pv])
a=0xa4be+128*2;p=m[a]+256*m[a+1];ht=m[p];full=(ht+15)//16*16
rom=bytearray((root/'gen/assets.bin').read_bytes());bank=3+len(rom)//16384;data=bytearray();desc=[]
for rgb in [(0,255,0),(255,0,0),(0,255,255),(255,255,0)]:
 color=int(np.argmin(np.sum((pal-np.array(rgb))**2,axis=1)));im=np.zeros((full,16),dtype=np.uint8)
 for row in range(ht):
  for x in range(16):
   if m[p+1+row*2+x//8]&(128>>(x&7)):im[full-1-row,x]=color
 b=bytearray([ht,full//16])
 for y in range(0,full,16):
  for x in (0,8):
   for dy in range(16):
    for plane in range(4):
     v=0
     for dx in range(8):v|=((int(im[y+dy,x+dx])>>plane)&1)<<(7-dx)
     b.append(v)
 desc.append('{%d,0x%04x,%d}'%(bank,0x8000+len(data),len(b)));data.extend(b)
rom.extend(data+bytes(16384-len(data)));(root/'gen/assets.bin').write_bytes(rom)
(root/'gen/assets.h').write_text(h+'\nconst Blob key_blobs[4]={'+','.join(desc)+'};\n')
