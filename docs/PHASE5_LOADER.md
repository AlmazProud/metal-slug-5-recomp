# Phase 5: Metal Slug 5's MAME set decrypted at load

**State:** in progress (started 2026-10-18).

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
