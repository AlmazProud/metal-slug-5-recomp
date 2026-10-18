# CLAUDE.md: Metal Slug 5 native port

Native Windows port of Metal Slug 5 (Neo Geo MVS, 2003, MAME set `mslug5`) by **progressive
static recompilation**, following the method of the finished Metal Slug X and Metal Slug 3 ports:
the 68000 code is translated to C, the Neo Geo hardware is reimplemented as a native runtime, and
everything is verified against MAME.

- Metal Slug X: https://github.com/AlmazProud/metal-slug-x-recomp, local copy in
  `C:\Projecto Decompile\repo`.
- Metal Slug 3: https://github.com/AlmazProud/metal-slug-3-recomp, local copy in
  `C:\Projecto Decompile\MS3_Port\repo`, v1.2.0 (commit `7c327dc`). **The base of this project:**
  its runtime and frontend are already generic (game descriptor + per-game profile).

Both repositories are **read-only for this project**: code is copied from them (MIT, Copyright (c)
2026 AlmazProud) and adapted here.

Goal: the same result as Metal Slug 3 v1.2.0. The game identical to MAME 0.289 (RAM, palette,
image per frame and audio sample by sample, verified by automatic tests); Metal Slug 3's complete
frontend; a loader for the MAME set (zip or loose files, recognised by CRC / SHA-1 and decrypted at
load); an interpreter-only release in a new repository `AlmazProud/metal-slug-5-recomp`.

**The difference from Metal Slug 3: there is only the MAME set.** No GOG or Steam release, so no
decrypted copy to compare with. The decryption is learned from MAME as a black box (synthetic
patterns) and checked against the regions MAME decrypts from the real set, dumped with Lua.

## Mandatory rules

1. **Bring your own ROM.** The repo never contains ROMs, BIOS, graphics, audio or extracted or
   decrypted data. They are read from `..\roms\` at run time and validated by hash. The
   `.gitignore` is a whitelist; the pre-commit hook (`tools/check_commit.py`) rejects binaries,
   files over 1 MB and ROM copies (zip members included); `tools/audit.py` runs before any
   publication, with the ROM search on. Encryption key tables, if needed, are the only possible
   exception, and **the user decides** (as with CMC42 in Metal Slug 3).
2. **MAME only as hardware documentation and oracle.** No MAME code is copied or read; behaviour
   is learned by black-box probing. Permissively licensed libraries are preferred, each
   documented in `THIRD_PARTY.md`.
3. **Everything is verified against MAME:** traces, RAM and palette per VBlank, image fingerprints
   per frame, audio with `-wavwrite`. Always fix the date (`--date`) when comparing runs.
4. **Stack:** C17, CMake, Ninja, llvm-mingw and SDL3; analysis tools in Python 3. All tools are
   shared in `C:\Projecto Decompile\tools`. No downloads without asking the user.
5. **Language:** the assistant always talks to the user in Spanish. Everything in the repository
   (code, identifiers, comments, docs, commit messages) is written in English. The frontend is
   English and Spanish.
6. This file and the phase's doc are updated when each phase closes.
7. **Commits:** small, author `Alan Jair Zavala Martinez <alvineslomejor@gmail.com>` (set with
   `git config --local`), message ending in
   `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
8. **Nothing public** (GitHub repository, releases, any push) without the user's explicit
   confirmation.
9. **Metal Slug X and Metal Slug 3 must not break:** `mslugx.exe` and `mslug3.exe` stay as
   regression targets when their ROMs are present; after any change to shared code their tests
   must pass.
10. If a tool fails because of disk space, tell the user before looking for a workaround.
11. Build folders always go in `repo\build`, `repo\build-dist` or `repo\build-*`.

**Way of working:** one phase at a time. Before writing code, present a short plan and wait for
the OK. When a phase or stage closes, report what works, what is missing, the risks and the next
step, and wait for approval.

## Structure

```
C:\Projecto Decompile\
  tools\        portable tools, shared with the Metal Slug X and Metal Slug 3 ports
  repo\         Metal Slug X port (read-only)
  MS3_Port\     Metal Slug 3 port (read-only); its roms\mame\neogeo holds the BIOS used here
  MS5_Port\
    repo\       this repository
    roms\       user's ROMs (outside the repo): mslug5.zip, neogeo\ (BIOS), later the regions
                MAME decrypts (decrypted\), + MANIFEST.sha256
    analysis\   analysis output and MAME runs        logs\   logs
    INSTALL.bat, env.ps1, env.bat, README.md   (copies from repo\setup\)
repo\
  setup\        installer (setup.ps1, versions.json, env.*, record_game.bat, sdl3_test\)
  src\cpu\      dispatcher, 68000 state, Musashi fallback            (imported from Metal Slug 3)
  src\neogeo\   Neo Geo runtime (bus, LSPC, RTC, scheduler, ROMs, sound), shared by the three games
  src\port\     SDL3 frontend (menus, configuration, headless mode), shared
  src\games\    one folder per game: game.c (NgGame), profile.c (GameProfile), sounds.c
  tools\        analysis, recompiler (recomp68k\), MAME Lua scripts (mame\), verification,
                audit.py, check_commit.py, hooks\; Phase 0: verify_set.py, probe_decryption.py,
                pvc_banks.py
  tests\        differential\ and lockstep\, loader\
  external\     Musashi, ymfm, z80.h, stb_truetype, fonts
  docs\         ROM_MAP.md, PHASE1_IMPORT.md; ADPCM_B.md and QOL_FEATURES.md (shared code, from
                Metal Slug 3)
```

Build (environment active): `cmake -S repo -B repo\build -G Ninja -DCMAKE_BUILD_TYPE=Release`,
`cmake --build repo\build`, `ctest --test-dir repo\build` (`-L mslug5` / `-L mslug3` / `-L mslugx`).
Builds `repo\build\src\mslug5.exe` and, when the other ports' copies are there, the regression
targets `mslug3.exe` (`PD_MS3_ROMS` / `PD_MS3_ANALYSIS`, default `<parent>\MS3_Port\roms` and
`analysis`) and `mslugx.exe` (`PD_MSX_ROMS` / `PD_MSX_ANALYSIS`, default `<parent>\roms` and
`analysis`). Interpreter-only (distributable) build: `-B repo\build-dist -DPD_RECOMPILED=OFF`.
**Before closing any change to shared code: all Metal Slug 3 and Metal Slug X tests must pass.**

Activate the environment: `. "C:\Projecto Decompile\MS5_Port\env.ps1"` (PowerShell) or
`call "C:\Projecto Decompile\MS5_Port\env.bat"` (cmd). `PD_ROOT` is the workspace, `PD_TOOLS` the
shared tools, `PD_ROMS` the ROM folder. Verify: `MS5_Port\INSTALL.bat -VerifyOnly`. Copy the ROMs:
`INSTALL.bat -CopyRoms` (the set to `roms\mslug5.zip`, the BIOS to `roms\neogeo\`).

Oracle: `mame mslug5 -bios us -rompath "<workspace>\roms"`.

## Status by phase

| Phase | Status |
|---|---|
| Environment | **Closed** (2026-10-17). Verification 17/17 OK. ROMs copied to `roms\`. |
| 0. Reconnaissance (encryption schemes, black-box decryption, ROM map, NEO-PVC, oracle) | **Closed** (2026-10-18). See `docs/ROM_MAP.md`. All five regions decrypted as MAME does, byte for byte. |
| 1. Import Metal Slug 3's runtime and frontend with an empty `mslug5` descriptor and profile | **Closed** pending approval (2026-10-18). See `docs/PHASE1_IMPORT.md`. `ctest`: 85/85 (interpreter-only 81/81). |
| 2. Metal Slug 5 hardware in the interpreter (NEO-PVC, encrypted M1, PCM2, banking) | Pending. |
| 3. Analysis and recompilation | Pending. |
| 4. Profile and frontend | Pending. |
| 5. Loader (MAME set decrypted at load) | Pending. |
| 6. Publishing (`AlmazProud/metal-slug-5-recomp`) | Pending. |

### Phase 1: result

Details in `docs/PHASE1_IMPORT.md`.

- **Import:** Metal Slug 3 v1.2.0's code (commit `7c327dc`) in one unchanged commit; against the
  Metal Slug 3 and Metal Slug X copies it passed the same 84 tests (`repo\build-ms3`).
- **Three executables:** `mslug5.exe` (the product, interpreter only) and the regression targets
  `mslug3.exe` and `mslugx.exe`, built when their copies are next to this workspace.
- **`mslug5` descriptor:** the 13 cartridge files of MAME's set (CRC-32, SHA-1), `NG_CART_PVC`
  (not emulated yet), no fix banking, no PC release, `mame_encrypted`. The loader recognizes the
  set and stops: "MAME set found and verified (13 files, BIOS us), but its decryption is not in
  the runtime yet" (test `mslug5_roms_mame`). Empty profile (title only); version 0.1.0.
- **Shared code** (Metal Slug 3 and X unchanged): games without a PC release skip the DotEmu,
  GOG and Steam searches and get a "game not found" screen that only mentions the MAME set
  (English and Spanish); GOG's `sfix.sfix` (the workspace's BIOS files) is accepted after MAME's.
- **Not done here:** the tools still default to `--game mslug3`, and `pd_recompiled_program`
  expects a PC release's `<id>_game_m68k` (Phases 2-3); release tooling (Phase 6).

### Phase 0: result

Details in `docs/ROM_MAP.md`.

- **The set:** every game ROM of `mslug5`, `mslug5h`, `mslug5b` and `ms5plus` matches MAME 0.289
  by CRC-32 and SHA-1 (`tools/verify_set.py`).
- **Everything is transformed:** program (NEO-PVC), sprites and fix (CMC50, the fix taken from the
  C ROMs, 128 KB), M1 (CMC50) and V (PCM2). MAME's regions from the real set are dumped in
  `roms\decrypted\` (outside the repo, searched by the audit and the hook).
- **Decryption learned as a black box** (`tools/probe_decryption.py learn|check`, synthetic
  patterns, no MAME code read); each map reproduces MAME's region from the real set byte for byte
  and predicts a fresh random image:
  - program, sprites, fix and ADPCM: affine (input unit, bit permutation, XOR);
  - the M1: a byte permutation keyed by the 16-bit sum of the file's first 64 KB, learned for the
    real key (0x1FCD) with synthetic images made to have that sum.
- **Independent check:** MAME's regions built from the `mslug5b` bootleg (already decrypted data)
  give the same 64 MB of sprites and the same ADPCM (254 of 256 blocks).
- **NEO-PVC as the game uses it:** only the bank registers `0x2FFFF0`/`0x2FFFF2`; the window
  0x200000 shows the region from the byte offset `0x100000 + (V >> 8)`, V = `F2:F0` (checked on
  every value MAME can map); the game uses `F2` = 0x1000-0x3000 (banks 0x200000-0x5FFFFF hold
  data). A boot check writes 7 to `0x2FFFF0` and 0x000A to `0x25FFF0`; the values read back from
  `0x2FFFF0` (0x0000, then 0x00A0) need probing in Phase 2.
- **Z80:** only the four default NEO-ZMC banks (64 KB of the 512 KB M1). **Fix:** 128 KB, no fix
  banking.
- **Developer menu** strings (`SET DEBUG DIP`, `TEST STAGE`, `STAGE SELECT`, `SOUND TEST`) and
  references to `0x10FE80` and `0x10F000`, as in Metal Slug 3: to be used from Phase 4.
- **Oracle:** `mame mslug5 -bios us -rompath roms` boots to the title, the attract demo and a
  scripted game (Mission 1), with sound (44 of 62 s).
- Tools added: `verify_set.py`, `probe_decryption.py`, `pvc_banks.py`; Lua: `dump_region.lua`,
  `screenshots.lua`, `trace_pvc.lua`, `pvc_bank_map.lua`, `trace_z80_banks.lua`.

### Environment phase: result

- Workspace `C:\Projecto Decompile\MS5_Port\` with `repo\`, `roms\`, `analysis\`, `logs\`.
- **Shared tools**, already installed (nothing downloaded): `INSTALL.bat -VerifyOnly` passed
  17/17: 7-Zip 26.04, Python 3.14.8 + pip, CMake 4.4.4, Ninja 1.13.2, clang 23.1.3, Java 21, MAME
  0.289, MinGit 2.56, GitHub CLI 2.102, ImHex 1.38.1 (portable), SDL3 3.4.18 (configure, build and
  window) and Ghidra headless (nothing left outside its folder).
- Copied from the Metal Slug 3 repo (v1.2.0) and adapted:
  - `setup\`: `-CopyRoms` takes the MAME set (`-RomSet`, default `MS5_Port\mslug5.zip`) and the
    BIOS folder (`-Bios`, default the Metal Slug 3 workspace's `roms\mame\neogeo`); `-Yes` skips
    the question; `record_game.bat` runs `mslug5` with `-rompath roms`;
  - `.gitignore` (adds `mslug5_*`, `analysis/`, `*.lo`, `*.sfix`, `*.npz`, `*.npy`),
    `.gitattributes`, `LICENSE` (MIT, AlmazProud), `THIRD_PARTY.md` (tools only for now);
  - `tools/audit.py` (executable `mslug5.exe`; the ROM search now reads every file under `roms\`,
    subfolders included, and every member of the zips there), `tools/check_commit.py` (also
    hashes the zip members) and the hook. Checked: the hook rejects a binary, a file over 1 MB
    and a copy of a BIOS file.
- **ROMs:** `roms\mslug5.zip` and `roms\neogeo\` (4 BIOS files), identical to their sources, with
  `MANIFEST.sha256`. `mame -verifyroms` finds every game file of `mslug5`, `mslug5h`, `mslug5b`
  and `ms5plus` correct; only `sfix.sfix` and `sm1.sm1` differ (the known stand-ins).
- Root copies: `INSTALL.bat`, `env.ps1`, `env.bat`, `README.md`, `grabar_partida.bat`.

## The MAME set (`mslug5.zip`, merged, MAME 0.289)

From `mame -listxml` (to be checked by CRC and SHA-1 in Phase 0):

| Set | Files | Notes |
|---|---|---|
| `mslug5` (NGM-2680, the target) | `268-p1cr/p2cr` (4 + 4 MB, `maincpu`), `268-m1` (512 KB, region `audiocrypt`), `268-v1c/v2c` (8 + 8 MB), `268-c1c..c8c` (8 x 8 MB) | no S1: the fix comes from the C ROMs |
| `mslug5h` (clone) | `268-p1c/p2c` | another program revision; the rest shared |
| `mslug5b` (bootleg) | P1 1 MB + P2 4 MB, S1 128 KB, M1 128 KB (`audiocpu`), V1-V4 (4 x 4 MB), C1-C8 | parts look already decrypted: cross-check only |
| `ms5plus` (bootleg) | P1 1 MB + P2/P3 2 MB, S1 128 KB | C, M1 and V shared with `mslug5` |

Confirmed in Phase 0 (`docs/ROM_MAP.md`): NEO-PVC program (encryption + byte-offset banks),
CMC50 sprites and fix, CMC50 M1 (keyed by the data), PCM2 V ROMs.

BIOS: no `neogeo.zip`. The Metal Slug 3 workspace's files are used (`sp-u2.sp1`, `000-lo.lo`,
`sm1.sm1`, `sfix.sfix`): `sfix.sfix` is GOG's, 28 bytes different from MAME's, and `sm1.sm1` is a
stand-in (the first 128 KB of Metal Slug 3's M1); MAME warns and boots.

## Lessons from Metal Slug 3 (apply them)

- **Lua in MAME:** subscriptions and taps in global variables; a fresh nvram folder per run;
  Windows paths, not `/c/...`; MAME reruns the autoboot script after a soft reset (guard it with a
  global); write taps on the LSPC registers `0x3C0000-3` never fire: use the debugger trace
  (`beamx`/`beamy`, `totalcycles`). Big-endian regions compose words big-endian.
- **MAME timing already reproduced in the runtime:** watchdog reset (counts from the write
  access), MOVEM video write order, Z80 interrupts two T-states early, 68000 commands one cycle
  into the access, MAME's ADPCM-B, SSG soft reset. If Metal Slug 5 diverges, suspect these first.
- **MAME's scheduler:** rare ~2-cycle shifts of raster interrupts (0.5 % in Metal Slug 3's final
  boss) are a known difference: bound them in time and ask the user before chasing them.
- **Known residue:** some VBlanks differ only in the stack (MAME takes the interrupt one
  instruction later); listed per run (`*_known_vblank.txt`) after a byte-by-byte check.
- **Reaching sections without playing:** look for a developer mode / debug dips / stage select
  before recording long games. `PD_POKE` takes hexadecimal values.
- **Editing:** bash heredocs break `\n` inside C strings and Python scripts; write patch scripts
  with the Write tool and normalise CRLF/LF. `.bat` and `.ps1` files need CRLF.
- **The window executable** has no stderr (GUI subsystem): debug to a file and remove it before
  committing. Window tests (`PD_WINDOW_TEST`, `PD_PREF`, `PD_LOAD_STATE`) need a fresh preference
  folder or a suitable `start_screen`; extras are processed in order.
- **Run-ahead:** disable every hook (`ng_before_input_read`, `ng_on_sound_command`,
  `ng_hook_word`, `ng_on_vblank_ack`), no audio in the frames run ahead, and run it after queueing
  the real audio.
- **Boss Rush:** the recompiled code reports the function's entry or resume point as the PC, so
  PC ranges do not work; a RAM write hook (`ng_hook_word`) on the section start bytes did.
