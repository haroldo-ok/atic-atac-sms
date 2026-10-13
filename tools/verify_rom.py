#!/usr/bin/env python3
from pathlib import Path
import json,struct,hashlib,re
root=Path(__file__).resolve().parents[1]
r=(root/'AticAtac.sms').read_bytes();o=(root/'gen/original.bin').read_bytes()
assert len(r)==2*1024*1024
assert r[0x7ff0:0x7ff8]==b'TMR SEGA'
assert r[0x7fff]==0x4f
checksum=(sum(r[:0x7ff0])+sum(r[0x8000:0x20000]))&65535
assert checksum==struct.unpack_from('<H',r,0x7ffa)[0]
assert r[0x3000:0x3194]==o[0x7ee6:0x807a], 'Original dispatch table was damaged'
assert r[0x600d:0x7c19]==o[0x600d:0x7c19], 'Castle template or room lists changed'
manifest=json.loads((root/'gen/manifest.json').read_text())
assert len(manifest['room_details'])==151
assert max(v['tiles'] for v in manifest['room_details'])<260
assert manifest['actor_frames']==161
header=(root/'gen/assets.h').read_text()
for bank,addr,size in re.findall(r'\{(\d+),0x([0-9a-f]+),(\d+)\}',header):
 bank,addr,size=int(bank),int(addr,16),int(size)
 if bank:assert bank*16384+addr-32768+size<=len(r) and addr+size<=0xc000
symbols={n:int(a,16) for n,a in re.findall(r'DEF (\S+) 0x([0-9A-Fa-f]+)',(root/'AticAtac.noi').read_text())}
ram_end=symbols['s__INITIALIZED']+symbols['l__INITIALIZED']
assert ram_end<0xc400
results={}
for name in ['mechanics','win','characters','serf','pause','hardware','rooms','weapons','trapdoor']:
 log=(root/f'shots/{name}-test.log').read_text();assert 'RESULT: ALL PASSED' in log;results[name]='PASS'
report={'rom_bytes':len(r),'sha256':hashlib.sha256(r).hexdigest(),'sega_header':'PASS','checksum_128k':checksum,'castle_template_and_room_lists_unchanged':True,'full_dispatch_table_preserved':True,'room_entries_converted':151,'original_actor_frames_converted':161,'colour_key_variants':4,'original_trapdoor_animation_frames':128,'ram_end':hex(ram_end),'sprite_pattern_pool':'260-315 (56 tiles)','background_room_tiles':'0-259','panel_tiles':'316-407','dynamic_hud_tiles':'408-447','emulator_tests':results,'physical_hardware_tested':False,'full_unstaged_playthrough':False}
(root/'TEST-REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
print('ROM/data integrity checks PASS; all 9 emulator test suites PASS; RAM end',hex(ram_end))
