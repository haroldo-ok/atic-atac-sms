# Attribution — smstest headless emulator

This directory bundles a minimal headless Sega Master System emulator used to
playtest homebrew ROMs automatically (no GUI, no human).

## Licences

- `smstest.c`, `prof_report.py`, `prof2.py`, `Makefile` and `selftest/` — the SMS
  wrapper (Sega mapper, VDP mode-4 renderer, joypad, PSG sink), the playtest
  script interpreter and its tools, by **Haroldo-OK**, originally from
  `jill-of-the-jungle-sms` (https://github.com/haroldo-ok/jill-of-the-jungle-sms).
  **MIT licence, Copyright (c) 2026 Haroldo-OK — see `LICENSE`.** You may ship it
  with your own projects (keep `LICENSE` with it).
- `z80.c`, `z80.h` — Z80 CPU core by **superzazu** (Nicolas Allemand),
  https://github.com/superzazu/z80. **MIT licence, Copyright (c) 2019 Nicolas
  Allemand — see `LICENSE.z80`.** Modified here with optional `on_call` /
  `on_ret` hooks for the call-graph profiler.

If you copy the harness into a project, copy `LICENSE` and `LICENSE.z80` with it.

## History

The profiler, `pause` (NMI), `psglog`/`psgstop`, `dumpstate`, and the
8-sprites-per-scanline / BG-priority screenshot fidelity were upstreamed from the
harness in Haroldo-OK's `flashback-sms` port (itself built on this skill).
`prof_report.py` was added alongside to attribute profile buckets to symbols.

Cartridge RAM, the call-graph profiler (`cgstart`/`cgstop`/`cgdump` + `prof2.py`,
with the Z80 core's call/return hooks), `expectpace`, `spmin`, `hooklog`,
`shots`, `frames`, `timers` and the debug ports 0x04/0x06 come from the harness
in Haroldo-OK's `out-of-this-world-sms`; garbage-on-power-up RAM from
`flashback-sms`. The `expectpace` threshold default was changed from 28 to 27
cycles (`pacemin`, `SMSTEST_PACE`) to match devkitSMS's own RST 18h spacing.

Game Gear mode (12-bit CRAM with the byte latch, the Start button on port 0x00,
160x144 screenshots), per-scanline palette and horizontal-scroll snapshots, and the
banked-symbol fix in `prof2.py` come from the harness in Haroldo-OK's
`jazz-jackrabbit-gg`. `liverender`, `sym+N` addresses, the `s8` width and timer
maxima come from the patch in Haroldo-OK's `opensosaria-sms`. The two were merged by
hand (both rewrote the renderer); `selftest/` was added to pin the raster and
beam-timing behaviour down.
