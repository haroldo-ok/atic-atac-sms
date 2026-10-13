# Atic Atac — Sega Master System port

**Playable 2 MiB `.sms` ROM, original Z80 game engine, Spec256-derived graphics, and reproducible source/conversion bundle.**

Open **`AticAtac.sms`** in a Master System emulator. The ROM uses the standard Sega mapper and the console's normal 8 KiB work RAM; it does not require cartridge RAM.

## Source archive quick start

The archive is **`AticAtac-SMS-source.zip`**. Extract it and work inside its top-level `AticAtac-SMS/` directory:

```sh
unzip AticAtac-SMS-source.zip
cd AticAtac-SMS

# Debian/Ubuntu build prerequisites:
sudo apt-get install sdcc gcc make python3-pip python3-venv
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt

make
make playtest
```

The archive includes the port source, original-instruction relocation reference, asset conversion scripts, supplied game inputs, preconverted asset banks, SDK sources and startup object, emulator test harness, nine test suites, license notices, test logs, and screenshots. A ready-to-play ROM and its debugger symbols are included as a convenience.

**`make` uses the included generated assets.** Use `make assets` only when you want to regenerate the graphics from `assets/source/`; this executes the original drawing routines and takes several minutes. After regeneration, run `make` and `make playtest` again.

`SHA256SUMS.txt` records the files packaged in this archive. On Linux, run `sha256sum -c SHA256SUMS.txt` immediately after extraction to check the package contents, before rebuilding or changing files.

## Controls

| Control | Action |
|---|---|
| D-pad Left / Right on the title | Select Knight, Wizard, or Serf |
| Button 1 on the title | Start |
| D-pad in the castle | Move; diagonals supported |
| Button 1 in the castle | Fire the character's original weapon |
| Button 2 | Pick up / advance the original three-slot FIFO inventory and drop its oldest item |
| Console Pause / emulator Pause key | Pause / resume |
| Button 1 after game over or escape | Return to character selection |

Find the three A.C.G. key pieces, carry them in the correct inventory order, and escape through the A.C.G. door. Food restores life force; mushrooms and monsters are dangerous. Clocks, bookcases, and barrels retain the original character-specific passages.

## What was converted

- The original executable game logic, rather than a newly invented castle/adventure engine.
- The complete **5,488-byte castle template and original room-content lists**, unchanged in cartridge ROM.
- All **149 game rooms**, plus the special/unused entries in the **151-entry room table**.
- All **161 original actor frames**, including the three characters, weapons, enemies, food, mushrooms, keys, collectables, and animation pictures.
- Every furniture/door graphic and every orientation actually referenced by the castle; open/shut and timed-door variants.
- The original trapdoor-fall outline and all 128 frames of its `SPIRAL_FILL` attribute animation.
- The original parchment, font, menu illustrations, inventory, spare-life figures, score, clock, and roast/bones life-force display.
- Separate red, green, cyan, and yellow versions of the original shared key bitmap, selected from the live original key attribute.
- Original input, beeper, framebuffer, and writable-code interfaces replaced with native SMS services.

**No substitute shapes, placeholder artwork, placeholder rooms, or dummy quest logic are used.** The images come from the supplied snapshot and expanded graphics. Conversion aborts if a furniture orientation cannot be matched to the original renderer or if a room exceeds its allocated tile budget.

The input `.GF7` file is entirely zero. `.GFB` is a Spectrum ROM graphics overlay, not a second castle or actor atlas. These input files are retained in `assets/source/`, but an SMS port does not execute or render the Spectrum BASIC ROM.

## Native SMS implementation

Actors, weapons, loose objects, menu illustrations, inventory items, and spare-life figures use **VDP hardware sprites**. Rooms, furniture, parchment, score, clock, and the changing roast use background tiles.

| Resource | Allocation |
|---|---|
| Room patterns | Tiles 0–259; actual maximum 259 unique tiles including alternate-door patterns |
| Actor pattern cache | Tiles 260–315 |
| Parchment | Tiles 316–407 |
| Clock, score, and changing food display | Tiles 408–447 |
| Name table | VRAM `$3800` |
| Sprite attribute table | SMSlib's normal SAT |
| SMS platform globals | `$C000`–`$C216` |
| Original variables and drawing scratch replacements | `$C400` region |
| Stack top | `$C900` |
| Live castle records | `$CA90`–`$DFFF` |

The native game code continues to run on the SMS Z80. Its writable variables are relocated, template writes are redirected to live RAM, and its dispatch table is moved to fixed ROM because the mandatory Sega header would otherwise overwrite several collectable handlers. Platform code lives in the first ROM bank; the original engine occupies slots 1 and 2. Asset banks are mapped only from fixed platform code and restored before returning to the engine.

The clock hook schedules original game ticks at 50 Hz on NTSC and uses PAL detection. The room pass runs separately from the player/weapon tick. The renderer uses paced SMSlib transfers; large room loads happen with the display disabled. Sound commands are queued and driven by an eight-line PSG interrupt, including short pitch sweeps; the door rasp uses the PSG noise channel.

## Hardware-driven differences and verification limits

This is a port, **not a cycle-exact Spectrum emulator**:

- Expanded Spec256 colours are reduced to the SMS's 6-bit RGB and two 16-entry palettes.
- The pad replaces the Spectrum's keyboard/Kempston/cursor selection; the title labels describe SMS controls.
- Crowded scenes use rotating sprite/tile-cache arbitration. The hardware's eight-sprites-per-scanline limit can cause flicker or intermittent clipping.
- Speaker effects are translated to PSG tones/noise. They are not bit-identical recordings; a bounded sound-command queue can drop commands during unusually long bursts.
- Rendering cadence and transition/appearance timings are not cycle-identical. Initial key/door randomization uses the port's initialization and ROM contents, so its first castle is not guaranteed to match a particular Spectrum snapshot's first castle.
- **Tested in the bundled emulator, not on a physical console.** PAL detection is implemented, but the supplied automated harness runs NTSC.
- The escape test stages the key pieces before walking through the original exit. A complete, unstaged end-to-end playthrough has not been performed.

## Automated test results

`make playtest` builds the actual ROM and runs nine suites. All passed for the supplied ROM:

| Suite | Coverage |
|---|---|
| `mechanics` | Movement, original key pickup/FIFO advancement, a real room doorway, last-life hunger, game over, title return |
| `win` | Ordered A.C.G. inventory, original exit logic, congratulations screen |
| `characters` | Wizard selection, original character sprite range, movement |
| `serf` | Serf selection, original character sprite range, movement |
| `pause` | Console Pause NMI, pause/resume state |
| `hardware` | Beam-timed rendering, visible colours, PSG register logging, paced VRAM writes, stack watermark |
| `rooms` | All 149 game rooms; enemies suppressed and lives refreshed in the test harness while rooms are staged |
| `weapons` | Original weapon firing and small-monster scoring |
| `trapdoor` | Actual trapdoor entry, original 128-frame attribute animation, landing in the lower room, paced VRAM writes |

The integrity checker additionally verifies the Sega header/checksum, every asset bank boundary, RAM allocation, complete dispatch-table preservation, and byte equality of the original castle template and room lists.

See **`TEST-REPORT.json`** and the `shots/*-test.log` files. Screenshots in `shots/` are actual ROM emulator output, not mockups. The harness's staging commands are external tests, not cheats or special modes in the game.

### Included build verification

The source archive was extracted into a separate directory and successfully rebuilt with **SDCC 4.5.0**. All nine emulator suites and the ROM/data integrity checks passed from that extracted copy.

The included ROM is **2,097,152 bytes**. Its SHA-256 is:

```text
1b2948f5cee2f4170fdb73c63a3062dca50d746fc0997e02f8c029add01734e8
```

This identifies the supplied, tested build; a different compiler version may produce a different binary. As noted above, these checks do not constitute physical-hardware testing or an unstaged full-game playthrough.

## Build

Requirements: SDCC 4.2 or newer, `sdasz80`, `sdar`, GCC, Python 3, and the packages in `requirements.txt`.

```sh
# Debian/Ubuntu, if the cross compiler is not already installed:
sudo apt-get install sdcc gcc make python3-pip
python -m pip install -r requirements.txt
make
make playtest
```

The included SDK sources are rebuilt locally with your SDCC, avoiding the older archive/compiler calling-convention metadata mismatch. No network downloads are needed by `make` once the listed packages are installed.

The generated asset banks are included, so a normal build does not re-render every room. To regenerate them from the included user-supplied input files:

```sh
make assets       # several minutes: executes the original Z80 drawing routines
make
make playtest
```

`tools/convert.py` uses SkoolKit's Z80 simulator as a drawing oracle. It matches furniture bitmap symmetries against the actual game rasterizer, applies the expanded per-pixel colours, quantizes to real SMS colours, converts to VDP bitplanes, deduplicates tiles, and writes bank descriptors. `tools/add_food.py`, `tools/add_keys.py`, and `tools/add_fall.py` add dynamic HUD/key variants and the original trapdoor animation. `tools/pack_rom.py` records executable patches in `gen/patches.json` and packs the cartridge.

## Files and rights

- `AticAtac.sms`: playable cartridge image.
- `AticAtac.noi`: platform and original live-state symbols for debugging.
- `src/`: native SMS renderer, scheduler, PSG driver, and Z80 bridges.
- `tools/`, `vendor/sdk/`: converter, verifier, test emulator, and toolchain sources.
- `assets/source/`: the supplied source game files.
- `gen/`: generated banks, descriptors, manifest, and patch audit.
- `tests/`, `shots/`: scripted checks, logs, and screenshots.

**Atic Atac, its original executable, and original art remain copyrighted by their respective owners.** The provided commercial game data and ROM are for the requesting user's personal conversion/use; availability in a repository does not make them public domain. No rights to the original game or Spec256 artwork are granted by this bundle.

Credits:

- Original game: Ultimate / A.C.G., 1983.
- User-supplied expanded game data: https://github.com/mvvproject/Spec256-Games/tree/master/Atic%20Atac
- Development skill and test harness: https://github.com/haroldo-ok/sega-master-system-skill-for-claude
- devkitSMS / SMSlib: sverx, https://github.com/sverx/devkitSMS
- Original instruction references: pobtastic's Ultimate disassemblies, https://github.com/pobtastic/ultimate
- Additional analysis used during development: https://github.com/jonsole/zx-spectrum-disassemblies
- Spec256 palette: ZX-Poly resources, https://github.com/raydac/zxpoly
- Harness Z80 core: superzazu; included MIT license in `tools/harness/LICENSE.z80`.

Third-party tooling retains its own licensing. See the included license notices. The bundled startup object retains the devkitSMS GPL linking exception; it does not grant rights to the original game data.
