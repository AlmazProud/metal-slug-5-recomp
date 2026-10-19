# Phase 6: publishing on GitHub

**State:** in progress (started 2026-10-18). Nothing public without the user's explicit OK at each
step.

Metal Slug 3's method (`C:\Projecto Decompile\MS3_Port\repo\docs\PHASE6_RELEASE.md`):

| Stage | Content | Status |
|---|---|---|
| 1 | Documentation (`README.md`) and version 1.0.0 | Done |
| 2 | Audits (`tools/audit.py`): the whole history, the ROM search, personal data | Done |
| 3 | Packaging (interpreter-only zip), CI and a clean clone | Done |
| 4 | Publishing `AlmazProud/metal-slug-5-recomp`, each step with the user's OK | Waiting: GitHub CLI is not signed in |

Known exception for the audits: `src/games/mslug5/crypt_tables.h`, the decryption's key tables,
in the repository by the user's decision (Phase 5).

## Stage 1: documentation and version

- **`README.md`** (new, English): what the port is, the legal notice, quick start with the MAME
  set (the game has no PC release), features, controls, where the settings go, how it works and
  how it was verified, known differences (the audio is not sample-exact; Mission 5's middle
  bosses are not in Boss Rush), building, layout, licenses. A hidden comment at the top leaves
  room for the author's own note.
- **Version 1.0.0** (`src/port/version.h`): `mslug5.exe --version` says `metal-slug-5-recomp 1.0.0`.

## Stage 2: audits (`tools/audit.py`)

- **History:** every version of every file of every commit (343) is whitelisted text of at most
  1 MB without long hex, base64 or byte-array runs, and holds no run copied from the ROMs. The ROM
  search ran against Metal Slug 5's folder (the encrypted set, MAME's decrypted regions, the
  reference files, the BIOS), Metal Slug 3's and Metal Slug X's: no match.
- **One more exception:** `src/games/mslug5/crypt_tables.h`, the decryption's key tables (Phase
  5, the user's decision), listed in `BYTE_ARRAY_OK` with its reason, next to Metal Slug 3's CMC42
  tables that came with the import.
- **Personal data:** every commit's author and committer is Alan Jair Zavala Martinez; no user
  name, other mail or profile path in the history.

## Stage 3: packaging and CI

- **`tools/package_release.py`** builds `release/metal-slug-5-recomp-v1.0.0-win64.zip` (2.8 MB, 13
  files) from the interpreter-only build: `mslug5.exe`, `SDL3.dll`, `LICENSE.txt`,
  `THIRD_PARTY.md`, `README.txt`, the licenses and an empty `game/` folder with instructions for
  the MAME set. The release audit is clean against the three games' ROMs. Unpacked in an empty
  folder with `mslug5.zip` and the BIOS in `game/`, it reaches the start screen.
- **GitHub Actions** (`.github/workflows/build.yml`): builds and uploads `mslug5.exe`.
- **Clean clone:** without ROMs, analysis or the environment's variables, with only the
  toolchain and Python in the PATH, it configures and builds with no warnings; `--version` says
  1.0.0; the Metal Slug 3 and X targets and the tests are left out.
