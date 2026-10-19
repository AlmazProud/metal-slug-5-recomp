# Phase 5: Metal Slug 5's MAME set decrypted at load

**State:** closed (2026-10-18). `ctest`: 117/117 (interpreter-only: Metal Slug 5's 31/31).

Goal: `mslug5.exe` runs from the user's MAME set (`mslug5.zip` or loose files, recognized by
CRC-32 and SHA-1) decrypted at load, with the same bytes as the decrypted reference files of
Phases 2-4.

## Plan

1. Compact descriptions of Phase 0's black-box maps (`docs/ROM_MAP.md`): the program (NEO-PVC:
   a 32-word XOR and the address map), the ADPCM-A samples (PCM2: an 8-byte XOR and the address
   map), the sprites and fix (CMC50: tables like Metal Slug 3's CMC42) and the M1 (a byte
   permutation keyed by the data: its structure, time-boxed; if none is found, the user is told
   before going on).
2. The runtime's decryption (`src/games/mslug5/crypt.c`), the set converted to the runtime's
   layout and checked against the reference files' SHA-256.
3. Tests: the set zipped and loose loads the same bytes as the reference files; the usual runs
   unchanged.
4. The portable copy with the MAME set instead of the decrypted files.

**Key tables:** authorized by the user (2026-10-18), as in Metal Slug 3: the PVC and PCM2 XOR
keys, the CMC50 tables and the M1's description may be in the repository. They are learned from
black-box probes with synthetic patterns (no game data, no MAME code).

## Result

`mslug5.exe` runs from the user's MAME set (`mslug5.zip` with the BIOS, or the loose files),
decrypted at load in about a second: every region identical to the decrypted reference files,
so the recompiled program and the profile apply as before.

### The compact descriptions (`tools/learn_crypt5.py`, `src/games/mslug5/crypt_tables.h`)

Each checked on the whole of the user's set against the region MAME built from it (Phase 0's
dumps): all identical.

| Region | Description | Size of its tables |
|---|---|---|
| Program (NEO-PVC, 8 MB) | 8 blocks of 512 K words (output bits 19-21): input word = block base ^ a linear map of bits 0-18 (two layouts: block 0 and the others); the word's bits permuted (3 permutations, by bit 0 and the block) and XORed (128 words, by bits 0-3 and the block) | 8 + 38 + 48 + 16 + 128 entries |
| ADPCM-A (PCM2, 16 MB) | input byte = base + the weights of the output byte number's set bits (an addition mod 16 MB, as Metal Slug 3's NEO-SMA P1), XORed by bits 0-2 | 1 + 24 + 8 |
| Sprites (CMC50, 64 MB) and fix (128 KB) | Metal Slug 3's CMC42 form (three byte-level XOR steps on the unit address, byte order swaps, data XOR) with CMC50's tables; the fix is a linear map into the decrypted sprites | 17 x 256 + 18 |
| M1 (CMC50, 512 KB) | a byte permutation keyed by the 16-bit sum of the file's first 64 KB, learned for the real key (`0x1FCD`): each 64 KB bank stays in place; within bank k, the file address's bits A = {1,3,5,7,9,10,13,14} and B = the others give X = PA[A] ^ T1[B] and Y = PB[B] ^ T2[X] (two Feistel steps), placed at the bank's own region bits | 8 x (4 x 256 + 16) |

The header is 87 KB: the key tables the user authorized. The M1's tables are for the real
set's key only; the loader only accepts the set by its hashes, and refuses another key.

### Runtime

- `src/games/mslug5/crypt.c`: the four decryptions; `NgMameCrypt` gained two optional in-place
  hooks (M1, ADPCM) that `roms.c` calls after joining the M and V files (Metal Slug 3 and X: none).
- Tests: `mslug5_roms_mame` (the set loads, recompiled program and profile on),
  `mslug5_roms_mame_zip` and `_loose` (every region identical to the reference files,
  `PD_COMPARE_ROMS`); the interpreter-only build passes Metal Slug 5's 31 tests.
- The portable copy (`tools/make_portable.py`) takes the MAME set (`mslug5.zip` and the three
  BIOS files) instead of the decrypted files.
