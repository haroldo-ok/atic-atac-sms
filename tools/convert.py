#!/usr/bin/env python3
"""Extract original assets; original Z80 routines are the geometry oracle."""
from pathlib import Path
import json, struct, re, collections
import numpy as np
from PIL import Image
from skoolkit import CSimulator
from skoolkit.snapshot import Snapshot
from skoolkit.trace import Tracer
from skoolkit.simutils import SP, T, PC, IXh, IXl
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(__import__('sys').argv[1] if len(__import__('sys').argv)>1 else str(ROOT/'assets/source'))
m=list(Snapshot.get(str(SOURCE/'AticAtac.sna')).memory)
g=(SOURCE/'AticAtac.GFX').read_bytes()
pal=np.array(list((ROOT/'tools/spec256.raw.pal').read_bytes()),dtype=np.uint8).reshape(256,3)
def word(a):return m[a]+256*m[a+1]
def sms_rgb(rgb):return tuple(int(round(int(c)/85))*85 for c in rgb)
def cram(rgb):return sum((int(c)//85)<<(2*i) for i,c in enumerate(rgb))
def spec_attr(a):
 v=255 if a&64 else 170
 return (v if a&2 else 0,v if a&4 else 0,v if a&1 else 0)
def pixels(mem,width=192):
 out=np.zeros((192,width,3),dtype=np.uint8)
 for y in range(192):
  a=0x4000+(y&7)*256+((y>>3)&7)*32+(y>>6)*2048
  for xb in range(width//8):
   attr=mem[0x5800+(y//8)*32+xb];ink=spec_attr(attr);paper=spec_attr(((attr>>3)&7)|(attr&64))
   for b in range(8):out[y,xb*8+b]=ink if mem[a+xb]&(128>>b) else paper
 return out
base=m.copy();base[0x5cb0]=0xe9;base[0xea90:]=base[0x600d:0x757d]
def simcall(mem,entry,ix=None,stop=0x10):
 s=CSimulator(mem,state={'iff':0,'im':1,'tstates':0});s.set_tracer(Tracer(s,0,0,0,[0]*16,0,False))
 s.registers[SP]=0x5df0;s.memory[0x5df0]=stop&255;s.memory[0x5df1]=stop>>8
 if ix is not None:s.registers[IXh]=ix>>8;s.registers[IXl]=ix&255
 s.trace(entry,stop,0,12000000,False,None,None,None,None,None)
 if s.registers[PC]!=stop:raise RuntimeError(f'Oracle did not return: {entry:04x}, {s.registers[PC]:04x}')
 return list(s.memory)
def screen_clear(mem):mem[0x4000:0x5b00]=[0]*0x1b00

def raw_picture(ptr,furniture=False,attr=71):
 w=m[ptr] if furniture else 2;h=m[ptr+1] if furniture else m[ptr];data=ptr+(2 if furniture else 1)
 rgb=np.zeros((h,w*8,3),dtype=np.uint8);mask=np.zeros((h,w*8),dtype=np.uint8)
 for row in range(h):
  for xb in range(w):
   adr=data+row*w+xb
   for b in range(8):
    x=xb*8+b;y=h-1-row;bit=bool(m[adr]&(128>>b));c=g[(adr-0x4000)*8+7-b]
    mask[y,x]=255 if bit else 0
    # 0/255 retain the underlying Spectrum ink/paper semantics.
    rgb[y,x]=pal[c] if c not in (0,255) else (spec_attr(attr) if c==255 and bit else (0,0,0))
 return rgb,mask

def bbox(a):
 yy,xx=np.nonzero(a);return (int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)) if len(xx) else None

def fixture(mem,adr,typ,room):
 q=mem.copy();screen_clear(q);q[adr]=typ;q[0x5e14]=0
 q=simcall(q,0x91fe,adr)
 mono=pixels(q);om=np.zeros((192,192),dtype=np.uint8)
 for yy in range(192):
  aa=0x4000+(yy&7)*256+((yy>>3)&7)*32+(yy>>6)*2048
  for xx in range(192):om[yy,xx]=255 if q[aa+xx//8]&(128>>(xx&7)) else 0
 if not np.any(om):return mono
 p=word(0xa600+(typ-1)*2);rgb,mask=raw_picture(p,True,71)
 # Compare all eight rectangle symmetries against the original rasterizer.
 bo=bbox(om);ox,oy,ex,ey=bo;target=om[oy:ey,ox:ex]
 transforms=[lambda a:a,lambda a:np.fliplr(a),lambda a:np.flipud(a),lambda a:np.flipud(np.fliplr(a)),lambda a:np.rot90(a),lambda a:np.rot90(a,3),lambda a:np.transpose(a,(1,0,2)) if a.ndim==3 else a.T,lambda a:np.flipud(np.fliplr(np.transpose(a,(1,0,2)) if a.ndim==3 else a.T))]
 for transform in transforms:
  mm=transform(mask);bb=bbox(mm)
  if bb is None:continue
  x,y,x2,y2=bb
  if mm[y:y2,x:x2].shape==target.shape and np.array_equal(mm[y:y2,x:x2],target):
   rr=transform(rgb);out=np.zeros_like(mono);dx=ox-x;dy=oy-y
   for sy in range(rr.shape[0]):
    for sx in range(rr.shape[1]):
     xx=dx+sx;yy=dy+sy
     if 0<=xx<192 and 0<=yy<192:
      c=rr[sy,sx]
      # Original colour tables resolve monochrome pixels, including key doors.
      out[yy,xx]=c if np.any(c) else mono[yy,xx]
   return out
 raise RuntimeError(f'Furniture geometry mismatch room {room}, record {adr:04x}, type {typ}')

def variants(typ):
 if typ==1:return [1,0x22,0x23]
 if typ==2:return [2,0x20,0x21]
 if typ in (0x18,0x19):return [0x18,0x19]
 return [typ]

def choose_palette(images,required=()):
 counts=collections.Counter(sms_rgb(c) for im in images for c in im.reshape(-1,3) if np.any(c))
 chosen=[(0,0,0)]
 for c in required:
  if c not in chosen:chosen.append(c)
 # Greedy colour-error minimization over the 64 actual hardware colours.
 while len(chosen)<16 and counts:
  errors={c: min(sum((a-b)**2 for a,b in zip(c,k)) for k in chosen)*n for c,n in counts.items()}
  best=max(errors,key=errors.get)
  if errors[best]==0:break
  chosen.append(best)
 return chosen+[(0,0,0)]*(16-len(chosen))
def index_image(im,palette):
 p=np.array(palette,dtype=np.int32);d=im.astype(np.int32)[...,None,:]-p
 return np.argmin(np.sum(d*d,axis=-1),axis=-1).astype(np.uint8)
def tilebytes(im):
 out=bytearray()
 for y in range(8):
  for plane in range(4):
   v=0
   for x in range(8):v|=((int(im[y,x])>>plane)&1)<<(7-x)
   out.append(v)
 return bytes(out)

banks=[bytearray(16384) for _ in range(3)];descriptors={};curbank=3;data=bytearray()
def blob(name,b):
 global curbank,data
 if len(b)>16384:raise RuntimeError(f'{name} too large {len(b)}')
 if len(data)+len(b)>16384:
  banks.append(data+bytes(16384-len(data)));curbank+=1;data=bytearray()
 descriptors[name]=(curbank,0x8000+len(data),len(b));data.extend(b)

# Sprite atlas: every one of the original 161 actor frames, not invented art.
sprite_rgb=[];sprite_masks=[]
for i in range(161):
 rgb,mask=raw_picture(word(0xa4be+i*2),False,71);sprite_rgb.append(rgb);sprite_masks.append(mask)
sprite_palette=choose_palette(sprite_rgb,[(0,0,255),(255,0,0),(0,255,0),(0,255,255),(255,255,0),(255,255,255)])
sprite_heights=[]
for i,rgb in enumerate(sprite_rgb):
 h=len(rgb);sprite_heights.append(h);ht=(h+15)//16*16
 arr=np.zeros((ht,16),dtype=np.uint8);arr[ht-h:]=index_image(rgb,sprite_palette)
 # Native 8x16 sprite ordering, left pair then right pair per 16px row.
 b=bytearray([h,ht//16])
 for y in range(0,ht,16):
  for x in (0,8):
   b.extend(tilebytes(arr[y:y+8,x:x+8]));b.extend(tilebytes(arr[y+8:y+16,x:x+8]))
 blob(f'sprite_{i+1}',b)

manifest={'source':'AticAtac.sna + AticAtac.GFX','rooms':151,'actor_frames':161,'room_details':[],'palette':'Spec256 official raw palette, reduced to SMS 6-bit RGB'}
for room in range(151):
 mem=base.copy();screen_clear(mem);mem[0xea91]=room
 # ARRIVE_IN_ROOM has non-returning control flow; stop immediately after DRAW_ROOM.
 s=CSimulator(mem,state={'iff':0,'im':1,'tstates':0});s.set_tracer(Tracer(s,0,0,0,[0]*16,0,False));s.registers[SP]=0x5e00
 s.trace(0x9147,0x9156,0,12000000,False,None,None,None,None,None)
 mem=list(s.memory);outline=pixels(mem);images=[outline];fixtures=[]
 if room<150:
  lp=word(0x757d+room*2)
  while word(lp):
   initial=word(lp);adr=(initial-0x757d)&65535;lp+=2
   if mem[adr+1]!=room:adr+=8
   typ=mem[adr]
   if not typ or typ in (4,5,6,7,19,20,31):continue
   vs=variants(typ);ims=[fixture(mem,adr,t,room) for t in vs]
   fixtures.append((adr,vs,ims));images+=ims
 palette=choose_palette(images)
 bg=outline.copy()
 for adr,vs,ims in fixtures:
  im=ims[vs.index(mem[adr])];mask=np.any(im!=0,axis=2);bg[mask]=im[mask]
 dictionary=[];lookup={}
 def tiles(im):
  arr=index_image(im,palette);result=[]
  for y in range(0,192,8):
   for x in range(0,192,8):
    b=tilebytes(arr[y:y+8,x:x+8])
    if b not in lookup:lookup[b]=len(dictionary);dictionary.append(b)
    result.append(lookup[b])
  return result
 bgmap=tiles(bg);basecount=len(dictionary);metadata=bytearray([len(fixtures)])
 for adr,vs,ims in fixtures:
  maps=[]
  for im in ims:
   full=bg.copy()
   # Erase the base fixture's complete rectangular footprint before compositing.
   union=np.any(np.stack(ims)!=0,axis=(0,3));full[union]=outline[union]
   mask=np.any(im!=0,axis=2);full[mask]=im[mask];maps.append(tiles(full))
  changed=[j for j in range(576) if any(mm[j]!=bgmap[j] for mm in maps)]
  metadata.extend(struct.pack('<HB',adr-0x2000,len(vs)))
  for typ,mm in zip(vs,maps):
   metadata.extend(struct.pack('<BB',typ,len(changed)))
   for j in changed:metadata.extend(struct.pack('<HH',j,mm[j]))
 if len(dictionary)>448:raise RuntimeError(f'Room {room} needs {len(dictionary)} BG tiles')
 blob(f'room_{room}',bytes(cram(c) for c in palette)+struct.pack('<H',len(dictionary))+b''.join(dictionary)+struct.pack('<576H',*bgmap)+metadata)
 manifest['room_details'].append({'room':room,'tiles':len(dictionary),'fixtures':len(fixtures),'base_tiles':basecount})
 if room%25==0:print('room',room,'tiles',len(dictionary),flush=True)
 if room==0:
  Image.fromarray(bg).resize((384,384)).save(ROOT/'shots/oracle-room0.png')

# Original parchment, font, title and HUD furniture.
panel=np.zeros((192,64,3),dtype=np.uint8)
for y in range(24):
 for x in range(8):
  k=m[0xb32a+y*8+x]
  for dy in range(8):
   adr=0xb03a+k*8+dy
   for dx in range(8):
    c=g[(adr-0x4000)*8+7-dx]
    if c not in (0,255):panel[y*8+dy,x*8+dx]=pal[c]
    elif m[adr]&(128>>dx):panel[y*8+dy,x*8+dx]=(255,170,0)
panelpal=choose_palette([panel]);panelidx=index_image(panel,panelpal);pd=[];pm=[];pl={}
for y in range(0,192,8):
 for x in range(0,64,8):
  b=tilebytes(panelidx[y:y+8,x:x+8])
  if b not in pl:pl[b]=len(pd);pd.append(b)
  pm.append(pl[b])
# Panel uses sprite palette on background tiles, allowing two independent palettes.
# Quantize to the same sprite palette used by actors so no palette conflicts occur.
panelidx=index_image(panel,sprite_palette);pd=[];pm=[];pl={}
for y in range(0,192,8):
 for x in range(0,64,8):
  b=tilebytes(panelidx[y:y+8,x:x+8])
  if b not in pl:pl[b]=len(pd);pd.append(b)
  pm.append(pl[b])
blob('panel',struct.pack('<H',len(pd))+b''.join(pd)+struct.pack('<192H',*[x+0x800 for x in pm]))
blob('font',bytes(m[0xbf4c:0xc124]))
# Keep original actor bitmap/height sources accessible in unused slot-1 ROM.
sp=0x4000;copies={};original=bytearray(m)
for i in range(161):
 p=word(0xa4be+i*2);size=1+2*m[p]
 if p not in copies:copies[p]=sp;original[sp:sp+size]=bytes(m[p:p+size]);sp+=size
 original[0xa4be+i*2:0xa4c0+i*2]=struct.pack('<H',copies[p])
assert sp<=0x6000
(ROOT/'gen/original.bin').write_bytes(original)
banks.append(data+bytes(16384-len(data)))
(ROOT/'gen/assets.bin').write_bytes(b''.join(banks[3:]))
# ROM packing keeps only descriptors in fixed code; no linker bank tricks required.
def desc(n):return '{%d,0x%04x,%d}'%descriptors[n]
h='typedef struct { unsigned char bank; unsigned int address, size; } Blob;\n'
h+='const Blob room_blobs[151]={'+','.join(desc('room_'+str(i)) for i in range(151))+'};\n'
h+='const Blob sprite_blobs[162]={{0,0,0},'+','.join(desc('sprite_'+str(i)) for i in range(1,162))+'};\n'
h+='const unsigned char sprite_palette[16]={'+','.join(str(cram(c)) for c in sprite_palette)+'};\n'
h+='const unsigned char sprite_heights[162]={0,'+','.join(map(str,sprite_heights))+'};\n'
h+='const Blob panel_blob='+desc('panel')+';\nconst Blob font_blob='+desc('font')+';\n'
(ROOT/'gen/assets.h').write_text(h)
manifest['rom_banks']=len(banks);manifest['max_room_tiles']=max(r['tiles'] for r in manifest['room_details']);manifest['panel_tiles']=len(pd)
(ROOT/'gen/manifest.json').write_text(json.dumps(manifest,indent=2))
print('Converted',manifest['rooms'],'rooms, all',len(sprite_rgb),'frames;',len(banks),'banks, panel',len(pd),'tiles')
