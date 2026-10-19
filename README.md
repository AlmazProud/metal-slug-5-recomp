# metal-slug-5-recomp

<!-- A word from the author: room for the author's own note, as in metal-slug-3-recomp. -->

A native Windows port of **Metal Slug 5** (Neo Geo MVS, 2003), built by statically recompiling
the game's 68000 program to C and reimplementing the Neo Geo hardware around it. It follows the
method of [metal-slug-x-recomp](https://github.com/AlmazProud/metal-slug-x-recomp) and
[metal-slug-3-recomp](https://github.com/AlmazProud/metal-slug-3-recomp), whose runtime and
frontend it shares.

**Bring your own copy.** This repository and its releases contain no part of the game: no code,
graphics, sound or BIOS. The port reads them at run time from a copy you own.

> Metal Slug 5 is © SNK CORPORATION. This is an unofficial fan project, not affiliated with or
> endorsed by SNK.

## Quick start

1. Download the latest zip from [Releases](https://github.com/AlmazProud/metal-slug-5-recomp/releases)
   and unzip it anywhere.
2. Have a copy of the game. Metal Slug 5 has no PC release: the port runs the **arcade board
   dump** (MAME's `mslug5` set, MAME 0.289): put `mslug5.zip` and `neogeo.zip` (or their files) in
   `game\`.
3. Run `mslug5.exe`. If it cannot find the game, drop the game's folder or zip on the window,
   or press ENTER to choose a folder. It remembers the choice.

The game files are recognized by their hashes (CRC-32 and SHA-1), not by their names. The set is
encrypted (NEO-PVC program, CMC50 graphics and sound program, PCM2 samples); the port decrypts it
on load, in about a second. The BIOS files it needs are the MVS BIOS (`sp-u2.sp1`), `000-lo.lo` and
`sfix.sfix`, all in MAME's `neogeo.zip`.

## Features

- **Arcade-exact game logic,** verified frame by frame against MAME (see *How it was verified*).
- **Modern frontend** with remastered menus in English and Spanish, usable with keyboard,
  gamepad or mouse:
  - start screen with **Continue** (the game is autosaved every minute and on quit);
  - pause menu;
  - 9 save-state slots;
  - settings for video, audio, game, controls and system.
- **Game modes:**
  - **Arcade:** a whole game with the original rules, 0, 1, 3, 5 or infinite continues, and a
    results page;
  - **Mission:** start at any mission you have reached;
  - **Boss Rush:** the five main bosses in a row with one credit (unlocked by finishing the
    game in Arcade or Mission mode).
- **Records:** best time and score per mission, Arcade's best score, Boss Rush's best time.
- **Boss health bar** (optional).
- **Video:**
  - 4:3 or square pixels, integer scaling up to 8K;
  - sharp, smooth or raw pixel filters;
  - scanlines and fullscreen;
  - a CRT effect (arcade monitor, TV or soft): scanlines, phosphor mask, glow and an optional
    curved screen;
  - V-sync that keeps audio in step on 60 Hz and high-refresh monitors.
- **Controls:**
  - keyboard and gamepad for two players, remappable;
  - autofire per player;
  - gamepad rumble, which you can set per sound in the sound menu.
- **Run-ahead** (optional, off by default): the game's reaction to a button is shown a frame
  sooner by emulating ahead, without changing the game.
- **Quality of life:** fast boot (skips the BIOS screen), fast forward, pause when the window
  is not active, PNG screenshots.
- **Slowdown:** optional removal of the original slowdown (68000 at 2x or 4x speed).
- **Red blood:** the game's own hidden BLOOD option.
- **Music and sounds menu:** every track, effect and voice of the game (440 sounds), with
  per-sound names and rumble.
- **The developers' own debug tools:** the hidden developer menu (stage select, debug switches
  such as invincibility and hit boxes).
- **Cheats:** start mission, weapons, bombs, lives, soldier, the fat form, spawning vehicles.
- **Debug panel (F3):** FPS, game logic rate, 68000 load, sprite and palette viewers.

## Controls

| Neo Geo | Player 1 keyboard | Player 2 keyboard | Gamepad |
|---|---|---|---|
| Joystick | Arrow keys | I J K L | D-pad |
| A (shoot) | Z | A | X / Square |
| B (jump) | X | S | A / Cross |
| C (grenade) | C | D | B / Circle |
| D | V | F | Y / Triangle |
| Start | 1 | 2 | Start |
| Coin | 5 | 6 | Back / Select |
| Autofire | B | G | RB / R1 |

| Key | Action |
|---|---|
| Esc (gamepad: Guide, or Back + Start) | Menu |
| F5 / F9 | Save / load state |
| F7 / F8 | Previous / next save slot |
| P | Pause |
| Tab (gamepad: right trigger) | Fast forward (held) |
| F11 or Alt+Enter | Fullscreen |
| F12 (gamepad: Share) | Screenshot |
| F2 | Board test button (service menu: difficulty, lives...) |
| F3 | Debug panel |
| F4 | Developers' menu (with developer mode on, during a mission) |

Every control and shortcut can be changed in **Settings > Keyboard** and **Settings > Gamepad**.

Settings, saves, records and screenshots are kept in `%APPDATA%\ProjectoDecompile\mslug5\`. If
you create a folder named `save` next to the executable, they are kept there instead, so the port
is portable (for example on a USB drive).

## How it works

1. **Analysis.** The game's 68000 program was mapped with a recursive disassembler and with
   execution traces from MAME (1.4 billion traced instructions: the game runs from its fixed
   program area; the NEO-PVC chip's banked area holds data).
2. **Recompilation.** Every instruction is translated to C. The translation keeps the 68000's
   exact cycle counts and interrupt timing.
3. **Runtime.** The Neo Geo hardware is a native runtime written for this project:
   - memory map and the cartridge's NEO-PVC chip (its RAM and byte-offset program banking);
   - the LSPC video chip (sprites, fix layer, line timing and interrupts);
   - the real-time clock and the watchdog;
   - the Z80 sound CPU and the YM2610 sound chip.
4. **Loader.** MAME's encrypted set is decrypted with a compact description of the NEO-PVC,
   CMC50 and PCM2 schemes, learned from MAME as a black box with synthetic patterns (no MAME code
   was read or copied). The description's key tables are the only game-specific tables in the
   repository (`src/games/mslug5/crypt_tables.h`).

The released executable cannot contain the recompiled C code, because that code is derived
from the game. It runs the game's 68000 program through a cycle-exact interpreter instead, at
about 7 times real time on a modern PC. If you build from source with your own copy, you also
get the recompiled program, which is used when your copy matches the one it was generated from.

## How it was verified

MAME 0.289 was used as the reference, never as a source of code.
- **The comparison:** the port and MAME run the same inputs from the same state. Every frame's
  image and the RAM and palette at every vertical blank are compared.
- **Runs:** power-on and attract demo (10,007 frames); a game with a bot (9,001 frames); a
  13.4-minute game recorded by hand; scripted runs of Missions 2 to 5; every boss section
  reached through the developers' stage table; every debug option and cheat against a MAME run
  that does the same.

All of these are identical in image, both with the recompiled program and with the interpreter
alone. In RAM, a few vertical blanks differ only in the stack or in a word written a moment
apart, where MAME takes the interrupt one instruction apart; each one is listed and checked
byte by byte.

**Known differences:**
- **Audio:** the sound program writes the same commands to the sound chip, in the same order, as
  in MAME, but some of them a few microseconds apart, so the audio is not sample-exact (it sounds
  the same). It comes from how MAME aligns its CPUs at power-on.
- **Mission 5's middle bosses** are not in Boss Rush yet (not identified).

## Building from source (Windows)

1. Clone the repository into a folder, for example `C:\Projecto Decompile\MS5_Port\repo`.
2. Run `repo\setup\INSTALL.bat`. It downloads every tool into `tools\` from its official source,
   checks its hash, and needs no administrator rights. The tools are CMake, Ninja, llvm-mingw,
   SDL3, Python, MAME and Ghidra. MAME and Ghidra are only needed for the analysis and
   verification tools.
3. Activate the environment in PowerShell (`. .\env.ps1`) and build:

```
cmake -S repo -B repo\build-dist -G Ninja -DCMAKE_BUILD_TYPE=Release -DPD_RECOMPILED=OFF
cmake --build repo\build-dist
```

That is the distributable build: it needs no game files. A personal build with the recompiled
program needs your copy in `roms\` and the analysis listings. `CLAUDE.md` and the `docs/` folder
describe every phase of the project.

The same sources also build `mslug3.exe` and `mslugx.exe` as regression targets for the shared
runtime, when those projects' copies are next to this one; they are not part of the releases.

## Repository layout

| Path | Contents |
|---|---|
| `src/cpu` | dispatcher, interpreter glue, cycle tables |
| `src/neogeo` | hardware runtime and the copy loader |
| `src/games` | one folder per game: ROM catalog, decryption, game profile, sound names |
| `src/port` | the SDL3 frontend |
| `tools/` | analysis, recompiler (`recomp68k/`), MAME scripts and comparison tools |
| `tests/` | differential, lockstep and loader tests |
| `external/` | Musashi, ymfm, the Z80 core, stb_truetype and the menu fonts (`THIRD_PARTY.md`) |
| `docs/` | per-phase documentation |

## License

The port's code is MIT licensed (`LICENSE`). Third-party code keeps its own license
(`THIRD_PARTY.md`): Musashi (MIT), ymfm (BSD-3-Clause), floooh/chips z80.h (zlib),
stb_truetype (MIT / public domain), SDL3 (zlib), and the fonts Black Ops One and Chakra Petch
(SIL Open Font License 1.1).
