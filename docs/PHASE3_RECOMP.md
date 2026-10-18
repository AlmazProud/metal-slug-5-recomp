# Phase 3: analysis and recompilation of Metal Slug 5

**State:** ready to close (waiting for the user's approval).

## Plan

1. Where Metal Slug 5's 68000 runs in MAME (P1, the NEO-PVC window over P2, the BIOS, RAM), from
   traces of the attract and scripted runs.
2. Coverage and static analysis (`tools/coverage.py`, `tools/game_desc.py`, Ghidra cross-check):
   `docs/PHASE3_COVERAGE.md`.
3. Recompilation with `tools/recomp68k` (P1 and the BIOS, as for Metal Slug 3). If code runs from
   the P2 banks, the dispatcher is the user's decision. `pd_recompiled_program` must read the
   decrypted reference files instead of a PC release's `<id>_game_m68k`.
4. Tests: lockstep per run and image, RAM and palette against MAME for the recompiled build. The
   audio is deferred (Phase 2) and stays out of the pass criteria.
5. A game recorded by the user (`grabar_partida.bat`) for coverage and verification.

The distributable build stays interpreter-only (`-DPD_RECOMPILED=OFF`); the recompiled build is
the development and verification target, as in Metal Slug 3.

## Result so far

- **Where the code runs** (MAME, `docs/PHASE3_COVERAGE.md`): P1 and the BIOS. **No code runs from
  the NEO-PVC window** (1 472 M traced instructions in four runs), so the dispatcher did not
  change: P1 and the BIOS recompiled, everything else interpreted. Code in RAM (644 addresses,
  the attract's ROM checksum: the bulk readers at `0x10018C`/`0x1001A6`) stays interpreted.
- **Coverage** (`analysis/phase3/coverage_*.json`, all used by the build): the bot (180 s), the
  playback of the attract and scripted recordings and of the user's game `partida1`
  (`--playback <name>.inp`). The bot alone missed 528 addresses that the scripted game runs
  (they were interpreted); with the playbacks, 0 of them are left.
- **Analysis:** 64 700 P1 addresses executed in MAME, all reached by the static analysis; 0 bytes
  of code where MAME read data (`docs/PHASE3_COVERAGE.md`).
- **`mslug5.exe` recompiled** (the user's reference files' P1 and BIOS, by SHA-256):

  | Run | Frames | Recompiled dispatches | Interpreted steps | Time (interpreter only) |
  |---|---:|---:|---:|---|
  | scripted (`start`) | 9 001 | 5 874 408 | 3 334 | 7.2 s (19.6 s) |
  | `attract` | 10 007 | 5 454 566 | 23 189 514 (the RAM checksum) | 8.1 s |
  | `partida1` (the user's game) | 48 359 | 32 054 025 | 17 901 | 43.2 s (103.6 s) |

  The interpreted steps of the scripted run are dispatches at an expired cycle limit and a few
  BIOS and RAM instructions.
- **Against MAME:** `mslug5_attract_vs_mame` and `mslug5_start_vs_mame` give the same result as
  the interpreter (images identical, the same known stack-only VBlanks).
- **Lockstep** (`lockstep_mslug5_reset`, `lockstep_mslug5_game`): the machine model has the
  NEO-PVC (8 KB of RAM, byte-offset window, odd-offset words); dumps of version 3
  (`tools/mame/dump_state.lua` with `PD_PVC=1`) carry the window's P2 offset and the chip's RAM.
  The game dump is frame 8 000 of the scripted run (Mission 1). All points verified, final memory
  identical.
- **The user's game** (`partida1`, 13.4 min recorded with `grabar_partida.bat`; MAME reference
  by `mame_run.py --replay --name partida1`, test `mslug5_play_partida1_vs_mame`): images
  identical on all 48 358 frames; RAM and palette identical except 48 known VBlanks
  (`partida1_known_vblank.txt`), checked byte by byte: four events where MAME takes the VBlank
  one instruction apart and their residue in the dead stack (`0x10F28E-0x10F2FB`), plus one
  transient byte (`0x108D39` at VBlank 15271, written by the interrupted routine; equal again at
  the next VBlank). The same class as Metal Slug 3's 74 known VBlanks of its recording.
- **MAME is not deterministic at boot here:** two replays of the same recording differed at
  VBlanks 69-94 (RAM only, images identical), most likely MAME's uninitialized NEO-PVC RAM
  (docs/PHASE2_HARDWARE.md; not proven here). The reference is the replay that matches the port (the port clears
  that RAM, as MAME's other runs showed).
- `ctest`: **92/92**.

## Changes

- `tools/coverage.py`, `tools/mame/coverage.lua`: NEO-PVC (`PVC offset` lines, the bytes
  `0x2FFFF0-3` kept as `bus.c` does; P2 data reads as P2 offsets; the chip's RAM excluded);
  `--game mslug5` by default; the set from `roms\mame` or `roms\`.
- `tools/game_desc.py`: `pvc(game)`.
- `tests/lockstep`: NEO-PVC in `machine.c`, dumps of version 3, the `mslug5` tests.

## Pending

- More recordings when available (the other missions; Phase 4).
- The audio (deferred by the user, Phase 2).
