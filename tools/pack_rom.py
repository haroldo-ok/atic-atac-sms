#!/usr/bin/env python3
from pathlib import Path
import re,struct,json,hashlib
from skoolkit.z80 import Assembler
ROOT=Path(__file__).resolve().parents[1]
m=bytearray((ROOT/'gen/original.bin').read_bytes());assembler=Assembler();patches=[]
symbols={}
for line in (ROOT/'platform.noi').read_text().splitlines():
 match=re.match(r'DEF (\S+) 0x([0-9A-Fa-f]+)',line)
 if match:symbols[match[1]]=int(match[2],16)
def patch(a,b,reason):
 patches.append({'address':hex(a),'old':m[a:a+len(b)].hex(),'new':bytes(b).hex(),'reason':reason});m[a:a+len(b)]=bytes(b)
def relocate(v):
 if 0x5e00<=v<0x5e70:return v+0x6600
 if v in (0x5c78,0x5c79):return v+0x67f8
 if 0xea90<=v<=0xffff:return v-0x2000
 if 0x9481<=v<=0x9488:return v+0x300f
 return v
for line in (ROOT/'tools/reference.skool').read_text().splitlines():
 x=re.match(r'[bcwts* ]\$([0-9A-F]{4}) (.*?)(?:\s*;.*)?$',line)
 if not x:continue
 a=int(x[1],16);op=x[2]
 if not 0x7c19<=a<0xa4be or op.startswith(('DEFB','DEFW','DEFM')):continue
 # These 16-bit literal operands address RAM. Relative jumps never need relocation.
 new=re.sub(r'\$([0-9A-F]{4})',lambda z:'$%04X'%relocate(int(z[1],16)),op)
 if new!=op:
  b=assembler.assemble(new,a)
  if b:patch(a,b,'RAM relocation: '+op+' -> '+new)
def hook(a,name):patch(a,[0xc3]+list(struct.pack('<H',symbols['_bridge_'+name])),'SMS platform: '+name)
for a in [0x8093,0x809a,0x80aa,0x80b4,0x80c2,0x8b8a,0x91fe,0x9213,0x9489,0x9962,0x9980,0x9f4a,0x9f56,0x9fca,0xa00e,0xa01a,0xa13b,0xa185,0xa1ae,0xa1bf,0xa1c9,0xa1d3,0xa1f3,0xa1ff,0xa219,0xa240,0xa2ce,0xa311]:patch(a,[0xc9],'Spectrum display service replaced by native SMS renderer')
for a,n in [(0x7c19,'title'),(0x7c29,'title'),(0x7dc3,'main'),(0x9bea,'room'),(0x96af,'visit'),(0x93be,'controls'),(0x938b,'pickup'),(0x80cb,'clearvars'),(0x8cb7,'rise'),(0x8d45,'sink'),(0x8c35,'gameover'),(0x96ec,'win'),(0x973a,'fall'),(0x9522,'door_end'),(0xa3aa,'sound')]:hook(a,n)
# Original ROM trampoline is JP(HL), not a Spectrum ROM call.
for a in [0x7e90]:patch(a,[0xe9,0,0],'Replace original ROM JP(HL) trampoline')
# Room list entries remain pointers into the immutable template; change the bias.
for a in [0x7e98,0x9045]:patch(a,struct.pack('<H',0x957d),'Template to relocated live-record bias')
# Move template copy ahead of placement, then write key positions directly to RAM.
patch(0x7db1,assembler.assemble('CALL $8D61',0x7db1),'Copy castle before randomizing live keys')
patch(0x7db4,assembler.assemble('CALL $94B6',0x7db4),'Place ACG pieces in live RAM')
patch(0x7db7,assembler.assemble('CALL $98D2',0x7db7),'Place coloured keys in live RAM')
patch(0x94cc,struct.pack('<H',0xcaa9),'ACG live room field')
for a,v in [(0x98dc,0xcac1),(0x98ed,0xcac9),(0x98f0,0xce91),(0x9901,0xcad1)]:patch(a,struct.pack('<H',v),'Key placement writes live records, never cartridge ROM')
# Door noise bypasses the Spectrum ROM bitstream but uses the original BC parameters.
hook(0xa471,'noise')
# Flash raster writes must not address mapper or ROM.
patch(0x8c97,[0xc9],'HUD score flash handled by native display')
patch(0x8ca7,[0xc9],'HUD score flash handled by native display')
# Build native executable ROM: slot 0 SMS platform, slots 1-2 original engine.
assert symbols['s__CODE']+symbols['l__CODE']<0x3000, 'Platform overlaps relocated dispatch table'
platform=(ROOT/'platform.sms').read_bytes()
rom=bytearray(platform[:16384])+m[0x4000:0x8000]+m[0x8000:0xc000]+(ROOT/'gen/assets.bin').read_bytes()
# The SEGA header overlaps original actor dispatch entries at $7FF0.
# Move the COMPLETE 202-entry table to unused fixed ROM, not just the overlapping entries.
rom[0x3000:0x3194]=m[0x7ee6:0x807a]
rom[0x7e80:0x7e82]=struct.pack('<H',0x3000)
rom[0x7eae:0x7eb0]=struct.pack('<H',0x3144)
# Header lives inside original menu ROM. Restore its 16 bytes from platform build.
rom[0x7ff0:0x8000]=platform[0x7ff0:0x8000]
size=1
while size<len(rom):size*=2
rom.extend(bytes([255])*(size-len(rom)))
# Size code F checksums the first 128 KiB; the Sega mapper still addresses the full 2 MiB.
rom[0x7fff]=0x4f
checksum=(sum(rom[:0x7ff0])+sum(rom[0x8000:0x20000]))&65535
rom[0x7ffa:0x7ffc]=struct.pack('<H',checksum)
(ROOT/'AticAtac.sms').write_bytes(rom)
(ROOT/'gen/patches.json').write_text(json.dumps(patches,indent=2))
# Augment symbols with original live state and engine labels for emulator debugging.
noi='\n'.join(l for l in (ROOT/'platform.noi').read_text().splitlines() if l.startswith('DEF '))+'\n'
for n,a in {'player':0xca90,'player_room':0xca91,'player_x':0xca93,'player_y':0xca94,'health':0xc428,'lives':0xc421,'inventory':0xc430,'original_ticks':0xc412,'rooms_seen':0xc440}.items():noi+=f'DEF _{n} 0x{a:X}\n'
(ROOT/'AticAtac.noi').write_text(noi)
print(f'{len(rom)//1024} KiB ROM; {len(patches)} explicit platform/relocation patches; SHA256 '+hashlib.sha256(rom).hexdigest())
