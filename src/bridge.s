.module bridge
.area _CODE
.globl _bridge_room, _draw_room
_bridge_room:
push af
push bc
push de
push hl
push ix
push iy
exx
push bc
push de
push hl
exx
ex af,af'
push af
ex af,af'
call _draw_room
ex af,af'
pop af
ex af,af'
exx
pop hl
pop de
pop bc
exx
pop iy
pop ix
pop hl
pop de
pop bc
pop af
ret
.globl _bridge_pickup, _read_pickup
_bridge_pickup:
push af
push bc
push de
push hl
push ix
push iy
exx
push bc
push de
push hl
exx
ex af,af'
push af
ex af,af'
call _read_pickup
ex af,af'
pop af
ex af,af'
exx
pop hl
pop de
pop bc
exx
pop iy
pop ix
pop hl
pop de
pop bc
pop af
ret
.globl _bridge_controls, _read_controls
_bridge_controls:
push af
push bc
push de
push hl
push ix
push iy
exx
push bc
push de
push hl
exx
ex af,af'
push af
ex af,af'
call _read_controls
ex af,af'
pop af
ex af,af'
exx
pop hl
pop de
pop bc
exx
pop iy
pop ix
pop hl
pop de
pop bc
pop af
ld a,(#0xc47f)
ret
.globl _bridge_rise, _rise
_bridge_rise:
push af
push bc
push de
push hl
push ix
push iy
exx
push bc
push de
push hl
exx
ex af,af'
push af
ex af,af'
call _rise
ex af,af'
pop af
ex af,af'
exx
pop hl
pop de
pop bc
exx
pop iy
pop ix
pop hl
pop de
pop bc
pop af
ret
.globl _bridge_sink, _sink
_bridge_sink:
push af
push bc
push de
push hl
push ix
push iy
exx
push bc
push de
push hl
exx
ex af,af'
push af
ex af,af'
call _sink
ex af,af'
pop af
ex af,af'
exx
pop hl
pop de
pop bc
exx
pop iy
pop ix
pop hl
pop de
pop bc
pop af
ld a,(#0xc47e)
or a
jp nz,#0x8d5b
ret
.globl _bridge_clearvars, _clear_vars
_bridge_clearvars:
push af
push bc
push de
push hl
push ix
push iy
exx
push bc
push de
push hl
exx
ex af,af'
push af
ex af,af'
call _clear_vars
ex af,af'
pop af
ex af,af'
exx
pop hl
pop de
pop bc
exx
pop iy
pop ix
pop hl
pop de
pop bc
pop af
ret
.globl _bridge_sound, _request_sound, _sound_b, _sound_c
_bridge_sound:
ld a,b
ld (_sound_b),a
ld a,c
ld (_sound_c),a
push af
push bc
push de
push hl
push ix
push iy
exx
push bc
push de
push hl
exx
ex af,af'
push af
ex af,af'
call _request_sound
ex af,af'
pop af
ex af,af'
exx
pop hl
pop de
pop bc
exx
pop iy
pop ix
pop hl
pop de
pop bc
pop af
ret
.globl _bridge_main, _game_tick
_bridge_main:
ld sp,#0xc900
push af
push bc
push de
push hl
push ix
push iy
exx
push bc
push de
push hl
exx
ex af,af'
push af
ex af,af'
call _game_tick
ex af,af'
pop af
ex af,af'
exx
pop hl
pop de
pop bc
exx
pop iy
pop ix
pop hl
pop de
pop bc
pop af
jp 0x7dc6
.globl _bridge_title, _title
_bridge_title:
ld sp,#0xc900
ei
call _title
jp 0x7d9a
.globl _bridge_gameover, _gameover
_bridge_gameover:
ld sp,#0xc900
ei
call #0x96c9
call _gameover
jp _bridge_title
.globl _bridge_win, _win
_bridge_win:
ld sp,#0xc900
ei
call #0x96c9
call _win
jp _bridge_title
.globl _bridge_fall, _fall
_bridge_fall:
push af
push bc
push de
push hl
push ix
push iy
exx
push bc
push de
push hl
exx
ex af,af'
push af
ex af,af'
call _fall
ex af,af'
pop af
ex af,af'
exx
pop hl
pop de
pop bc
exx
pop iy
pop ix
pop hl
pop de
pop bc
pop af
jp 0x9117
.globl _bridge_door_end
_bridge_door_end:
ld a,h
cp #0xe0
ret nc
ex de,hl
jp 0x950b
.globl _native_frame
_native_frame:
push ix
push iy
call #0x7eb2
pop iy
pop ix
ret

.globl _bridge_visit, _visit_room
_bridge_visit:
push af
push bc
push de
push hl
push ix
push iy
exx
push bc
push de
push hl
exx
ex af,af'
push af
ex af,af'
call _visit_room
ex af,af'
pop af
ex af,af'
exx
pop hl
pop de
pop bc
exx
pop iy
pop ix
pop hl
pop de
pop bc
pop af
ret

.globl _bridge_noise, _request_noise
_bridge_noise:
ld a,b
ld (_sound_b),a
ld a,c
ld (_sound_c),a
push af
push bc
push de
push hl
push ix
push iy
exx
push bc
push de
push hl
exx
ex af,af'
push af
ex af,af'
call _request_noise
ex af,af'
pop af
ex af,af'
exx
pop hl
pop de
pop bc
exx
pop iy
pop ix
pop hl
pop de
pop bc
pop af
ret
