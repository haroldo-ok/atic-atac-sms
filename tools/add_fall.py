"""Convert the original trapdoor outline and SPIRAL_FILL attribute animation."""
from pathlib import Path
import re,struct,numpy as np
from skoolkit import CSimulator
from skoolkit.snapshot import Snapshot
from skoolkit.trace import Tracer
from skoolkit.simutils import SP,PC,T
root=Path(__file__).resolve().parents[1]
m=list(Snapshot.get(str(root/'assets/source/AticAtac.sna')).memory)
m[0x5cb0]=0xe9;m[0xea90:]=m[0x600d:0x757d];m[0xea91]=150
s=CSimulator(m,state={'iff':0,'im':1,'tstates':0});s.set_tracer(Tracer(s,0,0,0,[0]*16,0,False));s.registers[SP]=0x5e00
s.trace(0x9147,0x9156,0,12000000,False,None,None,None,None,None)
m=list(s.memory);dic=[bytes(32)];lookup={dic[0]:0};tm=[]
for cy in range(24):
 for cx in range(24):
  tile=bytearray()
  for dy in range(8):
   y=cy*8+dy;a=0x4000+(y&7)*256+((y>>3)&7)*32+(y>>6)*2048+cx
   tile.extend([m[a],0,0,0])
  tile=bytes(tile)
  if tile not in lookup:lookup[tile]=len(dic);dic.append(tile)
  tm.append(lookup[tile])
rom=bytearray((root/'gen/assets.bin').read_bytes());bank=3+len(rom)//16384;data=bytearray()
def put(b):
 global bank,data
 if len(data)+len(b)>16384:rom.extend(data+bytes(16384-len(data)));data=bytearray();bank+=1
 d='{%d,0x%04x,%d}'%(bank,0x8000+len(data),len(b));data.extend(b);return d
room=bytes([0,63]+[0]*14)+struct.pack('<H',len(dic))+b''.join(dic)+struct.pack('<576H',*tm)+bytes([0]);rd=put(room)
m[0x5800:0x5b00]=[0]*768;frames=[]
for i in range(128):
 v=71 if i%8==0 else 0
 for a in [0x596b,0x596c,0x598b,0x598c]:m[a]=v
 q=CSimulator(m,state={'iff':0,'im':1,'tstates':0});q.set_tracer(Tracer(q,0,0,0,[0]*16,0,False));q.registers[SP]=0x5df0;q.memory[0x5df0]=16;q.memory[0x5df1]=0
 q.trace(0x9774,16,0,12000000,False,None,None,None,None,None)
 assert q.registers[PC]==16
 m=list(q.memory);out=[]
 for y in range(24):
  for x in range(24):out.append(tm[y*24+x] if m[0x5800+y*32+x] else 0)
 frames.append(put(struct.pack('<576H',*out)))
rom.extend(data+bytes(16384-len(data)));(root/'gen/assets.bin').write_bytes(rom)
h=(root/'gen/assets.h').read_text();a=h.index('const Blob room_blobs[151]={')+len('const Blob room_blobs[151]={');b=h.index('};',a);entries=re.findall(r'\{[^}]*\}',h[a:b]);entries[150]=rd
h=h[:a]+','.join(entries)+h[b:];h+='\nconst Blob fall_blobs[128]={'+','.join(frames)+'};\n';(root/'gen/assets.h').write_text(h)
print('Original falling-room outline:',len(dic),'tiles; SPIRAL_FILL:',len(frames),'frames')
