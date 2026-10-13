#include <SMSlib.h>
#include "../gen/assets.h"
#define MEM(a) (*(volatile unsigned char *)(a))
#define V(a) MEM(0xc400+(a))
#define FRAME MEM(0xc470)
#define PLAYER ((volatile unsigned char *)0xca90)
#define SPR_START 260
#define SPR_END 316
#define PANEL_START 316
#define DIGIT_START 408
#define FOOD_START 420
__sfr __at(0x7f) PSG;
unsigned char game_state, selected_character, room_number, paused;
unsigned int rendered_frames;
unsigned char last_digits[12];
unsigned char last_room=255, last_food=255, last_types[16];
unsigned char slot_code[56], slot_source[56];
unsigned char used_codes[16], used_tiles[16], used_count, next_tile;
unsigned char key_colour;
unsigned char rotate_index, video_pal;
volatile unsigned char pending_ticks, video_phase;
volatile unsigned char audio_head, audio_tail, audio_active;
volatile unsigned int audio_remaining;
unsigned int audio_pitches[32], audio_lengths[32];
unsigned int keys;
unsigned char sound_b, sound_c;
const unsigned char ui_palette[16]={0,0x30,3,0x33,0x0c,0x3c,0x0f,0x3f,0x15,0x2a,0x07,0x1b,0x38,0x0b,0x2f,0x1f};
unsigned char SMS_VDPType(void);
void native_frame(void);
void enter_native(void);
void bridge_main(void);
void bridge_title(void);
void bridge_room(void);
void bridge_controls(void);
void bridge_pickup(void);
void bridge_sound(void);
void bridge_rise(void);
void bridge_sink(void);
void bridge_gameover(void);
void bridge_win(void);
void bridge_fall(void);
void bridge_door_end(void);
void bridge_clearvars(void);

unsigned int read16(const unsigned char *p) { return p[0]|((unsigned int)p[1]<<8); }
const unsigned char *map(const Blob *b) { SMS_mapROMBank(b->bank); return (const unsigned char *)b->address; }
void restore(void) {SMS_mapROMBank(2);}
void empty_screen(void) {SMS_VRAMmemsetW(0x3800,0,1536);SMS_initSprites();SMS_copySpritestoSAT();}
void font_setup(void) {
 const unsigned char *p=map(&font_blob);
 SMS_load1bppTiles(p,0,472,0,7);restore();
 SMS_VRAMmemset(59*32,0,32);
}
void text(unsigned char x,unsigned char y,const char *s) {
 SMS_setNextTileatXY(x,y);
 while(*s) {unsigned char c=*s++;if(c<32||c>90)c=32;SMS_setTile(c-32);}
}
void clear_cache(void) {unsigned char i;for(i=0;i<56;i++){slot_code[i]=0;slot_source[i]=255;}for(i=0;i<16;i++)last_types[i]=255;last_food=255;for(i=0;i<12;i++)last_digits[i]=255;}
void bg_room(unsigned char r) {
 const unsigned char *p,*tm;unsigned int n;
 unsigned char y,x;
 if(r>150)r=0;
 SMS_displayOff();p=map(&room_blobs[r]);SMS_loadBGPalette(p);n=read16(p+16);
 SMS_loadTiles(p+18,0,n*32);tm=p+18+n*32;
 for(y=0;y<24;y++){SMS_setNextTileatXY(0,y);for(x=0;x<24;x++){SMS_setTile(read16(tm));tm+=2;}}
 p=map(&panel_blob);n=read16(p);SMS_loadTiles(p+2,PANEL_START,n*32);tm=p+2+n*32;
 for(y=0;y<24;y++){SMS_setNextTileatXY(24,y);for(x=0;x<8;x++){SMS_setTile(read16(tm)+PANEL_START);tm+=2;}}
 SMS_loadSpritePalette(sprite_palette);
 restore();SMS_displayOn();clear_cache();last_room=r;room_number=r;
}
void visit_room(void) {unsigned char r=PLAYER[1];if(r<151)V(0x40+(r>>3))|=1<<(r&7);}
void draw_room(void) {
 unsigned char r=PLAYER[1],shape;
 V(0x14)=0;V(0x1a)=MEM(0xa854+r*2);shape=MEM(0xa855+r*2);
 V(0x1d)=MEM(0xa982+shape*6);V(0x1e)=MEM(0xa983+shape*6);
 bg_room(r);
}
void update_fixtures(void) {
 const unsigned char *p;unsigned char count,i,k,v,typ,n;unsigned int cell,tile,addr;
 p=map(&room_blobs[last_room]);p+=18+read16(p+16)*32+1152;count=*p++;
 for(i=0;i<count;i++) {
  addr=read16(p);p+=2;v=*p++;typ=MEM(addr);
  for(k=0;k<v;k++) {
   unsigned char vt=*p++;n=*p++;
   if(vt==typ && i<16 && last_types[i]!=typ) {
    unsigned char z;for(z=0;z<n;z++) {
     cell=read16(p+z*4);tile=read16(p+z*4+2);
     SMS_setTileatXY(cell%24,cell/24,tile);
    }
    last_types[i]=typ;
   }
   p+=((unsigned int)n)*4;
  }
 }
 restore();
}
void glyph(unsigned int tile,unsigned char c) {
 const unsigned char *p=map(&font_blob);if(c<32||c>90)c=32;
 SMS_load1bppTiles(p+(c-32)*8,tile,8,0,6);restore();
}
void hud(void) {
 unsigned char i,c,level;unsigned int tm;
 unsigned char digits[12];
 digits[0]='0'+V(0x3d);digits[1]='0'+(V(0x3e)>>4);digits[2]='0'+(V(0x3e)&15);
 digits[3]='#';digits[4]='0'+(V(0x3f)>>4);digits[5]='0'+(V(0x3f)&15);
 for(i=0;i<3;i++){c=V(0x2a+i);digits[6+i*2]='0'+(c>>4);digits[7+i*2]='0'+(c&15);}
 for(i=0;i<12;i++)if(last_digits[i]!=digits[i]){glyph(DIGIT_START+i,digits[i]);last_digits[i]=digits[i];}
 SMS_setNextTileatXY(25,8);for(i=0;i<6;i++)SMS_setTile(0x800+DIGIT_START+i);
 SMS_setNextTileatXY(25,10);for(i=0;i<6;i++)SMS_setTile(0x800+DIGIT_START+6+i);
 level=V(0x28)>>3;if(level>30)level=30;
 if(level!=last_food) {
  const unsigned char *p=map(&food_blobs[level]);SMS_loadTiles(p,FOOD_START,768);restore();
  for(i=0;i<4;i++){unsigned char x;SMS_setNextTileatXY(25,11+i);for(x=0;x<6;x++)SMS_setTile(0x800+FOOD_START+i*6+x);}
  last_food=level;
 }
 tm=0; /* keep the HUD entirely tile-based; actors cannot overwrite it */
}
unsigned char sprite_pattern(unsigned char code) {
 unsigned char i,rows,ht,skip,x,r,t,base,source;const unsigned char *p;
 if(!code||code>165)return 255;
 for(i=0;i<used_count;i++)if(used_codes[i]==code)return used_tiles[i];
 rows=(sprite_heights[code<=161?code:129]+7)>>3;
 if(!rows || next_tile+rows*2>56 || used_count==16)return 255;
 base=next_tile;used_codes[used_count]=code;used_tiles[used_count++]=base;
 p=map(code<=161?&sprite_blobs[code]:&key_blobs[code-162]);ht=p[1]*16;skip=(ht-rows*8)>>3;p+=2;
 for(r=0;r<rows;r++)for(x=0;x<2;x++) {
  source=skip+r;t=base+r*2+x;
  if(slot_code[t]!=code || slot_source[t]!=source*2+x) {
   SMS_loadTiles(p+(source>>1)*128+(source&1)*32+x*64,SPR_START+t,32);
   slot_code[t]=code;slot_source[t]=source*2+x;
  }
 }
 next_tile+=rows*2;restore();return base;
}
void actor(unsigned char code,unsigned char x,unsigned char y,unsigned char visible_height) {
 unsigned char t,r,rows,top,skip;
 if(!code||code>165)return;
 if(code==129){switch(key_colour&7){case 4:code=162;break;case 2:code=163;break;case 5:code=164;break;case 6:code=165;break;}}
 t=sprite_pattern(code);if(t==255)return;
 rows=(sprite_heights[code<=161?code:129]+7)>>3;top=y-rows*8+1;
 skip=0;if(visible_height && visible_height<sprite_heights[code])skip=(sprite_heights[code]-visible_height+7)>>3;
 for(r=skip;r<rows;r++) {
  unsigned char yy=top+r*8;
  if(yy<192){SMS_addSprite(x,yy,SPR_START+t+r*2-256);SMS_addSprite(x+8,yy,SPR_START+t+r*2+1-256);}
 }
}
void draw_monsters(unsigned char room) {
 unsigned char i;volatile unsigned char *q;
 for(i=0;i<8;i++){q=(volatile unsigned char *)(0xce60+(((i+rotate_index)&7)<<4));if(q[1]==room)actor(q[0],q[3],q[4],0);}
}
void draw_objects(unsigned char room) {
 unsigned char i,j;volatile unsigned char *q;
 for(i=0;i<118;i++){j=i+rotate_index;if(j>=118)j-=118;q=(volatile unsigned char *)(0xcaa8+((unsigned int)j<<3));if(q[1]==room&&q[0]!=0x31){key_colour=q[5];actor(q[0],q[3],q[4],0);}}
}
void sprites(void) {
 volatile unsigned char *q;unsigned char code,i,room=PLAYER[1];
 SMS_initSprites();used_count=0;next_tile=0;
 code=PLAYER[0];
 if(code==0x66||code==0x67)actor(PLAYER[7],PLAYER[3],PLAYER[4],PLAYER[6]);
 else actor(code,PLAYER[3],PLAYER[4],0);
 q=PLAYER+8;if(q[1]==room)actor(q[0],q[3],q[4],0);
 // Repeated lives share one pattern allocation, instead of three copies.
 for(i=0;i<V(0x21)&&i<3;i++)actor(selected_character*16+1,200+i*16,141,0);
 for(i=0;i<3;i++){key_colour=V(0x33+i*4);actor(V(0x32+i*4),200+i*16,44,0);}
 // Alternate room-object and monster priority so crowded rooms never permanently hide an item.
 if(rotate_index&1){draw_monsters(room);draw_objects(room);}else{draw_objects(room);draw_monsters(room);}
 rotate_index++;if(rotate_index==118)rotate_index=0;
 SMS_copySpritestoSAT();
}
void audio_tick(void) {
 unsigned int pitch;
 if(audio_remaining){audio_remaining--;return;}
 if(audio_head!=audio_tail){
  pitch=audio_pitches[audio_head];audio_remaining=audio_lengths[audio_head];audio_head=(audio_head+1)&31;
  if(pitch&0x8000){PSG=0x9f;PSG=0xe5;PSG=0xf4;}else{PSG=0xff;PSG=0x80|(pitch&15);PSG=(pitch>>4)&63;PSG=0x94;}audio_active=1;
 }else if(audio_active){PSG=0x9f;PSG=0xff;audio_active=0;}
}
void silence(void) {
 __asm di __endasm;
 audio_head=audio_tail=audio_active=0;audio_remaining=0;
 PSG=0x9f;PSG=0xbf;PSG=0xdf;PSG=0xff;
 __asm ei __endasm;
}
void request_sound(void) {
 // Queue every original beeper command, including sub-frame pitch sweeps.
 // Eight-line PSG interrupts provide much finer resolution than a frame-rate-only SFX player.
 unsigned int b=sound_b?sound_b:256,period,length;
 unsigned char next=(audio_tail+1)&31;
 period=(b*26+48)/31;if(!period)period=1;
 length=((unsigned long)sound_c*(b*26+48)+2399)/2400;if(!length)length=1;
 if(next==audio_head)return;
 audio_pitches[audio_tail]=period;audio_lengths[audio_tail]=length;audio_tail=next;
}
void request_noise(void) {unsigned char next=(audio_tail+1)&31;if(next==audio_head)return;audio_pitches[audio_tail]=0x8000;audio_lengths[audio_tail]=8;audio_tail=next;}
void frame_wait(void) {
 __asm ei __endasm;
 SMS_waitForVBlank();
 // 60 Hz console -> original 50 Hz game clock; PAL consoles need no skipped field.
}
void clock_irq(void) {
 video_phase++;if(video_phase==6)video_phase=0;
 if(game_state==1&&!paused&&(video_pal||video_phase!=0)&&pending_ticks<4)pending_ticks++;
}
void tick50(void) {
 while(!pending_ticks)frame_wait();
 __asm di __endasm;
 pending_ticks--;
 __asm ei __endasm;
 FRAME++;native_frame();
}
void game_tick(void) {
 keys=SMS_getKeysStatus();
 if(SMS_queryPauseRequested()){SMS_resetPauseRequest();paused=!paused;}
 if(paused){silence();do{frame_wait();}while(!SMS_queryPauseRequested());SMS_resetPauseRequest();paused=0;}
 tick50();
 if(PLAYER[1]!=last_room)draw_room();
 update_fixtures();hud();sprites();rendered_frames++;
 tick50();
}
void read_controls(void) {
 unsigned char a=31;keys=SMS_getKeysStatus();
 if(keys&PORT_A_KEY_RIGHT)a&=~1;if(keys&PORT_A_KEY_LEFT)a&=~2;
 if(keys&PORT_A_KEY_DOWN)a&=~4;if(keys&PORT_A_KEY_UP)a&=~8;
 if(keys&PORT_A_KEY_1)a&=~16;
 MEM(0xc47f)=a;
}
void read_pickup(void) {V(0x20)=(SMS_getKeysStatus()&PORT_A_KEY_2)?2:0;}
void rise(void) {
 unsigned char h;
 if(V(0x3c)){V(0x3c)--;return;}
 if(FRAME&3)return;
 PLAYER[6]++;h=sprite_heights[PLAYER[7]];
 if(PLAYER[6]>=h){PLAYER[0]=PLAYER[7];PLAYER[6]=0;PLAYER[7]=0;PLAYER[2]=0;}
}
void sink(void) {
 MEM(0xc47e)=0;
 if(!(FRAME&3))return;
 if(PLAYER[6])PLAYER[6]--;else MEM(0xc47e)=1;
}
void title(void) {
 unsigned char old=SMS_getKeysStatus();game_state=0;last_room=255;silence();SMS_displayOff();
 SMS_loadBGPalette(ui_palette);SMS_loadSpritePalette(sprite_palette);empty_screen();font_setup();SMS_displayOn();clear_cache();
 for(;;) {
  frame_wait();keys=SMS_getKeysStatus();
  if((keys&PORT_A_KEY_LEFT)&&!(old&PORT_A_KEY_LEFT)){if(selected_character)selected_character--;else selected_character=2;}
  if((keys&PORT_A_KEY_RIGHT)&&!(old&PORT_A_KEY_RIGHT)){selected_character++;if(selected_character==3)selected_character=0;}
  text(4,0,"ATICATAC GAME SELECTION");
  text(11,2,"MASTER SYSTEM PAD");text(11,5,"FIRE : BUTTON 1");text(11,8,"PICK : BUTTON 2");
  text(11,11,"KNIGHT");text(11,14,"WIZARD");text(11,17,"SERF");
  text(10,20,"BUTTON 1 TO START");text(0,23,"1983 A.C.G. ALL RIGHTS RESERVED");
  SMS_initSprites();used_count=0;next_tile=0;
  actor(0x32,32,79,0);actor(0x33,48,79,0);
  actor(0x4a,32,55,0);actor(0x4b,48,55,0);
  actor(0x48,32,28,0);actor(0x49,48,28,0);
  actor(1,40,103,0);actor(17,40,127,0);actor(33,40,151,0);
  SMS_copySpritestoSAT();
  SMS_setTileatXY(9,11,59);SMS_setTileatXY(9,14,59);SMS_setTileatXY(9,17,59);
  text(19,11,"        ");text(19,14,"        ");text(19,17,"        ");
  text(19,11+selected_character*3,"SELECTED");text(4,22,"LEFT/RIGHT TO SELECT");
  if((keys&PORT_A_KEY_1)&&!(old&PORT_A_KEY_1))break;
  old=keys;
 }
 V(0)=selected_character*8;FRAME=0;MEM(0xc471)=0x25;game_state=1;pending_ticks=0;clear_cache();
}
void summary(unsigned char won) {
 unsigned char i;unsigned int timer=0;game_state=won?3:2;silence();
 SMS_displayOff();SMS_loadBGPalette(ui_palette);empty_screen();font_setup();SMS_displayOn();
 text(6,5,won?"CONGRATULATIONS":"GAME OVER");if(won)text(5,7,"YOU HAVE ESCAPED");
 text(7,11,"TIME");text(7,13,"SCORE");text(7,15,"EXPLORED");
 for(i=0;i<3;i++){unsigned char c=V(0x2a+i);SMS_setTileatXY(16+i*2,13,'0'-32+(c>>4));SMS_setTileatXY(17+i*2,13,'0'-32+(c&15));}
 SMS_setTileatXY(16,11,'0'-32+V(0x3d));SMS_setTileatXY(17,11,'#'-32);SMS_setTileatXY(20,11,'#'-32);
 for(i=0;i<2;i++){unsigned char c=V(0x3e+i);SMS_setTileatXY(18+i*3,11,'0'-32+(c>>4));SMS_setTileatXY(19+i*3,11,'0'-32+(c&15));}
 i=V(0x54);SMS_setTileatXY(18,15,'0'-32+(i>>4));SMS_setTileatXY(19,15,'0'-32+(i&15));SMS_setTileatXY(20,15,'$'-32);
 text(5,20,"BUTTON 1 TO PLAY AGAIN");
 while(SMS_getKeysStatus()&PORT_A_KEY_1)frame_wait();
 do{frame_wait();timer++;}while(!(SMS_getKeysStatus()&PORT_A_KEY_1)&&timer<600);
}
void gameover(void){summary(0);}
void win(void){summary(1);}
void fall(void) {
 unsigned char i;silence();SMS_displayOff();bg_room(150);SMS_displayOn();
 SMS_initSprites();used_count=0;next_tile=0;
 for(i=0;i<V(0x21)&&i<3;i++)actor(selected_character*16+1,200+i*16,141,0);
 for(i=0;i<3;i++){key_colour=V(0x33+i*4);actor(V(0x32+i*4),200+i*16,44,0);}
 SMS_copySpritestoSAT();
 for(i=0;i<128;i++){
  const unsigned char *p;unsigned char y;
  frame_wait();FRAME++;
  p=map(&fall_blobs[i]);
  for(y=0;y<24;y++){SMS_loadTileMap(0,y,p,48);p+=48;}
  restore();PSG=0x80|(i&15);PSG=(i>>4)+2;PSG=0x95;
 }
 silence();last_room=255;
}
void clear_vars(void) {unsigned int i;for(i=0x10;i<0x200;i++)MEM(0xc400+i)=0;for(i=0;i<8;i++)MEM(0xc490+i)=MEM(0x9481+i);}
void main(void) {
 SMS_setSpriteMode(SPRITEMODE_NORMAL);SMS_useFirstHalfTilesforSprites(0);
 silence();video_pal=SMS_VDPType()&0x80;SMS_setFrameInterruptHandler(clock_irq);SMS_setLineInterruptHandler(audio_tick);SMS_setLineCounter(7);SMS_enableLineInterrupt();selected_character=0;clear_cache();
 __asm
 ld sp,#0xc900
 jp _bridge_title
 __endasm;
}
SMS_EMBED_SEGA_ROM_HEADER(9999,0);
