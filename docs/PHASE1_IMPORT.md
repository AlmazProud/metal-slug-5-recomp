# Phase 1: the Metal Slug 3 runtime and frontend, imported

**State:** closed, pending approval.

The code of the Metal Slug 3 port (v1.2.0), whose runtime and frontend were already generic (a game
descriptor and a game profile), now lives in this repository. One source tree builds three
executables:

- **`mslug5.exe`**, the product. Interpreter only. It recognizes the user's MAME set (every file
  by CRC-32 and SHA-1) and says that its decryption is not in the runtime yet: the set is not
  loaded (Phase 2 / Phase 5).
- **`mslug3.exe`** and **`mslugx.exe`**, regression targets, built only when those ports'
  workspaces are next to this one (`<parent>\MS3_Port\roms`, `<parent>\roms`), never released.
  Their tests against MAME guard the shared runtime and frontend.

## Import

- **One commit** (`Import the Metal Slug 3 port's code`) copies `src/`, `external/`, `tests/`,
  `tools/`, `CMakeLists.txt`, the GitHub Actions workflow and the docs that describe shared code
  (`docs/ADPCM_B.md`, `docs/QOL_FEATURES.md`) from
  https://github.com/AlmazProud/metal-slug-3-recomp at v1.2.0 (commit `7c327dc`), unchanged.
  - MIT license, Copyright (c) 2026 AlmazProud.
  - Kept from this repository: `tools/audit.py`, `tools/check_commit.py` (both also search zip
    members) and `tools/probe_decryption.py` (Metal Slug 5's probes); five identical files.
  - Not imported: Metal Slug 3's phase docs, ROM map and `docs/functions_p1.csv` (its analysis
    output). Code comments that cite `docs/PHASE*.md`, `docs/BOSS_RUSH.md` or `docs/ROM_MAP.md`
    for Metal Slug 3 facts refer to the Metal Slug 3 repository.
- **Baseline:** the imported code, built against the Metal Slug 3 and Metal Slug X copies
  (`repo\build-ms3`), passed the same **84 tests** as in its own repository.
- The Metal Slug 3 repository was not modified (still at `7c327dc`, clean working tree).

## What changed

| Where | Change |
|---|---|
| `CMakeLists.txt` | `PD_ROMS` / `PD_ANALYSIS` are Metal Slug 5's; `PD_MS3_ROMS` / `PD_MS3_ANALYSIS` (default `<parent>\MS3_Port\roms` / `analysis`) and `PD_MSX_*` the regression targets'. |
| `src/CMakeLists.txt` | `mslug5.exe` (installed by `cmake --install`); `mslug3.exe` only when its copy exists (`PD_HAVE_MSLUG3`), like `mslugx.exe`; test `mslug5_roms_mame`; Metal Slug 3 tests keep the label `mslug3`, Metal Slug 5's `mslug5`. |
| `tests/lockstep/CMakeLists.txt` | Metal Slug 3's lockstep only with `PD_HAVE_MSLUG3`. |
| `src/games/mslug5/` | `game.c`: the MAME set's 13 cartridge files (CRC-32, SHA-1), `NG_CART_PVC`, no fix banking, no PC release; `profile.c`: empty profile (title only). |
| `src/port/mslug5.rc` | executable properties. |
| `src/port/version.h` | 0.1.0 (0.x until the first release). |
| `neogeo.h` | `NG_CART_PVC` (not emulated yet); `NgGame.mame_encrypted`: the set needs a decryption the runtime does not have yet. |
| `roms.c` | A game without a PC release (`dotemu` names NULL, no GOG program hash) skips the DotEmu search; with `mame_encrypted` and no `crypt`, a complete, verified set is reported ("MAME set found and verified (13 files, BIOS us), but its decryption is not in the runtime yet") and not loaded. The PC releases' system fix (GOG's `sfix.sfix`, CRC `354029fc`, 28 bytes apart from MAME's) is accepted after MAME's: the workspace's BIOS files come from Metal Slug 3's GOG copy, for MAME and the port alike. |
| `find_game.c` | GOG, Steam and the usual install folders are only searched for games with a PC release. |
| `window.c`, `lang.c` | The "game not found" screen of a game without a PC release only mentions the MAME set (English and Spanish). |

Metal Slug 3's and Metal Slug X's behaviour is unchanged: their descriptors have PC releases and
no `mame_encrypted`, and MAME's `sfix.sfix` still comes first.

## Verification

| Build | Tests | Result |
|---|---|---|
| Baseline (`repo\build-ms3`, imported code, Metal Slug 3 + Metal Slug X) | 84 | **84/84** |
| Personal (`repo\build`: Metal Slug 5 interpreter only, Metal Slug 3 and X recompiled) | 84 + `mslug5_roms_mame` | **85/85** (before and after the "game not found" change) |
| Interpreter only (`repo\build-dist`, `-DPD_RECOMPILED=OFF`) | Metal Slug 3 and X's 80 + `mslug5_roms_mame` | **81/81**; `mslug5.exe` 2.0 MB |

- The "game not found" screen of `mslug5.exe` (`PD_FIND_TEST`) in English and Spanish: only the
  MAME set is mentioned.

- `mslug5.exe --roms roms`: "MAME set found and verified (13 files, BIOS us), but its decryption
  is not in the runtime yet". With the zip alone (no BIOS): "Incomplete MAME set: missing
  sfix.sfix, 000-lo.lo, an MVS BIOS (neogeo.zip)".

## Pending (later phases)

- **Phase 2:** the decryption in the runtime (or a decrypted reference copy, to decide), NEO-PVC
  banking and its readback, and then the game against MAME.
- **Tools that still default to Metal Slug 3** (`--game mslug3`): `analyze68k.py`,
  `audit_cycles.py`, `coverage.py`, `mame_run.py`, `recomp68k/program.py`,
  `ymprobe/run_probe.py`; `pd_recompiled_program` expects a PC release's `<id>_game_m68k`. They are
  adapted when Metal Slug 5 needs them (Phases 2 and 3).
- **Release tooling** (`package_release.py`, `make_portable.py`, the workflow): Phase 6.
