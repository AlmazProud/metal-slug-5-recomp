# ROM_MAP: MAME's `mslug5` set (Phase 0)

Source: the user's merged MAME 0.289 set `mslug5.zip` (copied to `roms\`), with the Neo Geo BIOS
files of the Metal Slug 3 workspace in `roms\neogeo\`. Oracle: MAME 0.289,
`mame mslug5 -bios us -rompath roms`.

**Main result:** every cartridge region of `mslug5` is transformed at load (program, sprites,
fix, Z80 program and ADPCM). All five transformations were learned from MAME as a black box
(synthetic patterns; no MAME code read) and each reproduces, from the real set, the region MAME
builds, byte for byte. There is no decrypted copy to compare with (no GOG or Steam release); the
reference is MAME's regions, dumped with Lua into `roms\decrypted\` (outside the repository; the
audit and the pre-commit hook search them too).

## The set

`tools/verify_set.py mslug5 mslug5h mslug5b ms5plus`: every game ROM of the four sets is in the zip
with the CRC-32 and SHA-1 of `mame -listxml`. Only the system files differ: `sfix.sfix` (GOG's,
28 bytes apart) and `sm1.sm1` (a stand-in), as in the Metal Slug 3 workspace.

| File | Bytes | MAME region | Transformation (Phase 0) |
|---|---|---|---|
| `268-p1cr.p1`, `268-p2cr.p2` | 4 MB + 4 MB | `cslot1:maincpu` (8 MB) | NEO-PVC program decryption: affine |
| `268-c1c.c1`...`268-c8c.c8` | 8 x 8 MB | `cslot1:sprites` (64 MB) | CMC50: affine |
| (none: no S1) | | `cslot1:fixed` (128 KB) | CMC50 fix taken from the sprite ROMs: affine |
| `268-m1.m1` | 512 KB | `cslot1:audiocrypt` (512 KB) -> `cslot1:audiocpu` (576 KB) | CMC50 M1: a byte permutation **keyed by the data** (below) |
| `268-v1c.v1`, `268-v2c.v2` | 8 MB + 8 MB | `cslot1:ymsnd:adpcma` (16 MB) | PCM2: affine |

Clone and bootlegs (cross-checks only, never a reference for the port):

- `mslug5h`: another program (`268-p1c/p2c`, 91 % of the bytes equal to `mslug5`'s files); same
  graphics, M1 and V.
- `mslug5b`: bootleg with its own P1 (1 MB) + P2 (4 MB), S1, a 128 KB M1, V1-V4 and C1-C8, already
  decrypted but reordered. MAME's regions built from it (`roms\decrypted\mslug5b\`) are an
  independent check of the decryption learned from `mslug5`:
  - **sprites: all 64 MB identical** to MAME's CMC50 decryption of `mslug5`;
  - **ADPCM: identical** except in 2 of 256 blocks of 64 KB;
  - program: its P1 matches `mslug5`'s decrypted 0-0xFFFFF at 99.9 % (the bootleg patches it),
    and its P2's four 1 MB blocks are `mslug5`'s 0x500000, 0x200000, 0x300000 and 0x400000;
  - fix 96 % and M1 54 % (identical up to 0x8000): the bootleg changes them.
- `ms5plus`: a hack with its own P (1 + 2 + 2 MB) and S1; C, M1 and V shared with `mslug5`.

## How the transformations were learned

`tools/probe_decryption.py learn TARGET` (`program`, `graphics`, `audio`, `adpcm`) builds a
complete `mslug5` set where the probed files hold synthetic patterns, MAME loads it, and
`tools/mame/dump_region.lua` dumps the regions right after start. Probes: all zeros, all ones,
three random images (GF(2) linearity: `f(a)^f(b)^f(a^b)^f(0) = 0`), one per address bit and one
per data bit. Model, checked on every probe: every output unit is `pi_i(input unit sigma(i)) XOR
c(i)`. The tool then predicts MAME's output for a fresh random image, and
`probe_decryption.py check TARGET` applies the maps to the real set and compares with the dumps.
The maps (`<region>_map.npz`) stay in `analysis\phase0\probe\`, never in the repository.

| Target | Runs | Linearity | Model | Prediction | Real set vs MAME |
|---|---|---|---|---|---|
| program | 44 | 0 units break it | each output word = an input word, one of 3 data permutations (identity; bits 12<->13 and 14<->15; bits 0<->1 and 2<->3), XOR on every word | 0 words differ | 4 194 304 / 4 194 304 words |
| graphics: sprites | 40 | 0 | each output byte = an input byte XOR k, no bit permutation | 0 | 67 108 864 / 67 108 864 |
| graphics: fix | (same runs) | 0 | 131 072 scattered bytes of the sprite image XOR k | 0 | 131 072 / 131 072 |
| adpcm | 38 | 0 | each output byte = an input byte XOR k, no bit permutation | 0 | 16 777 216 / 16 777 216 |
| audio (M1) | 7 | **breaks** (587 506 bytes) | keyed byte permutation, below | 0 | 589 824 / 589 824 |

### Structure seen so far (for the compact description, Phase 5)

- **Program:** the XOR depends only on address bits 0-3 and 19-21 (32 distinct words). The address
  map is not affine over GF(2) (Metal Slug 3's NEO-SMA map turned out to contain an addition).
- **ADPCM (PCM2):** the XOR depends only on address bits 0-2 (8 distinct bytes); the address map
  is not affine.
- **Sprites and fix (CMC50):** the XOR depends on every address bit, with the same statistics as
  Metal Slug 3's CMC42, which `learn_cmc.py` reduced to small tables.
- The decrypted 8 MB program, 64 MB sprites and 16 MB ADPCM are not something the repository can
  hold; Phase 5 needs a compact description, and any key table in it is the user's decision.

### The M1: a permutation keyed by the data

Observed with single-byte changes of a random M1 (`analysis\phase0\probe_m1x`):

- the 512 KB at `audiocpu` 0x10000 are a pure byte permutation of the file (same byte histogram,
  a changed byte moves to one place and keeps its value); `audiocpu` 0-0xFFFF repeats
  0x10000-0x1FFFF;
- a change in the file's first 64 KB changes the whole permutation, unless it keeps the 16-bit
  sum of those 64 KB (mod 0x10000): two changes with the same sum, or a change of the sum by
  exactly 0x10000, only move the changed bytes; a change of the sum by 4 with the same byte XOR
  changes everything. **Key = sum of the first 64 KB of the file, mod 0x10000** (0x1FCD for the
  real set).

So the permutation is learned for the real key only (`learn_keyed`): synthetic images whose key
is made equal by a block of compensation bytes; three images give every output byte's source
address as three base-256 digits; two rounds with disjoint compensation blocks, and each output
takes the source that reproduces all six probes. `audiocrypt` (the encrypted region as MAME keeps
it) is the file in its odd 64 KB blocks and differs in the even ones; it is not needed.

## The 68000 program region (`maincpu`, decrypted)

| Region offset | Content |
|---|---|
| `0x000000-0x0FFFFF` | P1, the fixed area (vectors: SP `0x10F300`, PC `0xC00402`; header `NEO-GEO`, NGH `0x0268`); data to `0xFBFB9` |
| `0x100000-0x1FFFFF` | all `0xFF` |
| `0x200000-0x5FFFFF` | four 1 MB banks with data (`0x2FFFF2` = 0x1000, 0x2000, 0x3000, 0x4000) |
| `0x600000-0x7FFFFF` | all `0xFF` |

Static scan of P1 (Capstone): no `JSR`/`JMP` into the window `0x200000-0x2FFFFF`; its 2 295
absolute references there are data accesses (`move.l`/`movea.l`/`move.w`/`lea` from the bank's
start `0x200000`, and the bank registers). The banks look like data only; Phase 3's coverage
will confirm it.

## NEO-PVC as the game uses it

Tools: `tools/mame/trace_pvc.lua` (attract mode and a scripted game), `tools/mame/pvc_bank_map.lua`
(every 16-bit value written to each bank register, the window sampled), `tools/pvc_banks.py`.

- **Accesses** in 400 s of attract mode and a game (Mission 1 until game over): only the bank
  registers `0x2FFFF0` and `0x2FFFF2` (911 772 writes; `0x2FFFF2` = 0x1000, 0x2000 or 0x3000,
  `0x2FFFF0` = 0); no colour pack/unpack registers.
- **Bank select:** the two words form V = `0x2FFFF2`:`0x2FFFF0`; the window shows the region from
  the **byte** offset `0x100000 + (V >> 8)`, past the end reading `0xFF`. Checked on all 65 536
  values of `0x2FFFF0` (with `0x2FFFF2` = 0x1000) and on `0x2FFFF2` = 0x0000-0x60FF (with
  `0x2FFFF0` = 0): every sample as predicted. An odd offset (e.g. `0x2FFFF0` = 0x0100) makes the
  68000's words straddle two of the region's words. Values from `0x2FFFF2` = 0x6100 on reach past
  the 8 MB and MAME reads outside its buffer and crashes; the game never uses them.
- **Boot check** (`0x866`-`0x882`, twice at the first boot, frames 280 and 283, which suggests a
  watchdog reset as in Metal Slug 3): the game saves `0x2FFFF0`, writes 7 to it, writes 0x000A to
  `0x25FFF0` (inside the window), and writes the saved value back. The first read gives 0x0000,
  the second 0x00A0, and a later checksum loop (PC `0x1001A6`, code in RAM) reads `0x2FFFF0` as
  0x00A0 although the game last wrote 0. Since the bank ignores the low byte of `0x2FFFF0`, the
  bank does not change; the read values must still be reproduced (Phase 2, by probing).
- **Top 8 KB:** the checksum loop reads `0x2FE000-0x2FFFFF` (twice): 0x0000 everywhere except the
  registers, which read back (`0x2FFFF2` = 0x1000, `0x2FFFF0` = 0x00A0).

## Z80 (NEO-ZMC)

`tools/mame/trace_z80_banks.lua`, 400 s with a game: the driver only sets the four default banks
(ports `0x08`-`0x0B` with high bytes `0x1E`, `0x0E`, `0x06`, `0x02`, 115 times each): it works in
the first 64 KB of the 512 KB M1. The runtime's full NEO-ZMC banking (Metal Slug 3) covers it
anyway.

## Fix layer

The cartridge fix is 128 KB (4 096 tiles): a tile number fits in VRAM's 12 bits, so **no fix
bank switching** is needed (Metal Slug 3's fix was 512 KB with bank switching).

## Developer menu (for later phases)

The program holds the developers' menu strings seen in Metal Slug X and Metal Slug 3:
`(PAUSE)`, `SET DEBUG DIP`, `TEST STAGE`, `COLOR BAR` (`0x9396`-`0x93D0`), `STAGE SELECT`
(`0xBEE1`, after `STAGE 5`) and `SOUND TEST` (`0xB41C`). P1 references the BIOS developer mode
`0x10FE80` four times (`0x2622`, `0x264C`, `0x266A`, `0x3B4A`) and the word `0x10F000` (Metal Slug
3's debug dips) 21 times. To be confirmed in MAME (Phase 4); it should reach every mission and
boss without recording games.

## The oracle

`mame mslug5 -bios us -rompath roms` boots: the first boot with an empty NVRAM (a full-screen
memory test), the warning screen, the SNK logo, the title and the attract demo
(`analysis\phase0\boot_montage.png`); a scripted coin and START give the game's "How to play",
Soldier Select and Mission 1 (`analysis\phase0\play_montage.png`, `snap_play\`). Audio over 62 s
(`-wavwrite`): sound in 44 seconds, from second 14 on. MAME warns about `sfix.sfix` and `sm1.sm1`.

## Risks

- **Compact description (Phase 5):** the address maps are not affine; the program and the ADPCM
  have tiny XOR keys, the sprites a CMC-style key. The M1 needs its permutation as a function of
  the key, or at least for the real key (the loader only accepts the real set's hashes anyway).
- **NEO-PVC readback:** the values read from `0x2FFFF0` after the boot check need probing.
- **Bootleg data** is reordered or patched: only MAME's regions built from it are compared.
