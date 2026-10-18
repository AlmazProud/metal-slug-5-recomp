# Phase 2: Metal Slug 5 hardware in the interpreter

**State:** ready to close (waiting for the user's approval). Image and RAM identical to MAME; the
audio is a known difference, deferred by the user to a later stage (below).

`mslug5.exe` (interpreter, no recompiled code yet) boots the decrypted reference files and runs
identical to MAME 0.289 in image on every frame and in work RAM and palette on every VBlank, except
VBlanks that differ only in the stack (MAME takes the VBlank one instruction apart), listed per run.

## The data the runtime loads

- **Decrypted reference files** (`tools/make_reference.py`): MAME's regions, dumped from the user's
  set (`roms\decrypted\`, Phase 0), converted to the runtime's layout (the DotEmu layout of the
  PC releases) and written to `roms\mslug5_*` (never versioned). The descriptor holds their
  SHA-256; `mslug5_roms_reference` checks them. The conversions are checked by round trip with
  Metal Slug 3's (verified) inverse conversions; the BIOS, system fix and zoom table files come
  out identical to the Metal Slug 3 GOG files. Until Phase 5, this is how the port gets the
  decrypted game; the MAME set itself is recognized and reported (`mslug5_roms_mame`).
- Games without a PC release (`ng_has_pc_release()`: no GOG id) describe these files as
  "Decrypted reference files (MAME's regions)", skip the GOG and Steam searches and get a "game
  not found" screen that only mentions the MAME set.
- **`sm1.sm1`** (MAME's sound BIOS stand-in): the first 128 KB of the decrypted M1, as the Metal
  Slug 3 workspace did with its own M1. The port has no SM1 and boots the Z80 from the M1; MAME
  must run the same code (before, the workspace had Metal Slug 3's).

## NEO-PVC (`bus.c`)

Learned from MAME as a black box with `tools/bus_probe.py` (`tools/mame/bus_probe.lua`: reads and
writes through MAME's handlers at a given frame, one fresh machine per probe):

- `0x2FE000-0x2FFFFF` is 8 KB of RAM over the top of the P2 window (whatever the bank). In MAME
  it is not initialized at power-on (one of four identical runs read garbage); the port clears it,
  which is what MAME showed in the recorded runs. It survives the watchdog reset.
- A write (word or byte) to `0x2FFFF0-0x2FFFF3` stores its bytes, then:
  - the window `0x200000-0x2FFFFF` shows the program from the **byte** offset
    `0x100000 + (F2 << 16 | F3 << 8 | F0)` (the bytes at `0x2FFFF2`, `0x2FFFF3`, `0x2FFFF0` as
    they are; Phase 0's sweep of every value is the same rule);
  - the chip rewrites the bytes: `F0` loses bit 0, `F1` reads `0xA0`, `F2` loses bit 7.
  Checked: written 0x0100 to `F0` shows offset +1, and a later write to `F2` shows +0 (the
  stored, masked byte); every high byte of `F0` reads back with bit 0 clear; `F2` = 0x8000 reads
  0x0000.
- With an odd offset the 68000's words straddle two of the program's words, as MAME reads its
  region; past the end of the program the window reads `0xFFFF`.
- The game's boot check (`0x866`-`0x882`) and its bank switches all behave as in MAME (the image
  and RAM comparisons below cover them). Writes to the ROM part of the window (the boot check's
  `0x25FFF0`) are ignored and counted as unmapped writes (3 per boot).
- Save states are version 5 (the PVC RAM is part of the machine).

## Verification

References: `tools/mame_run.py --game mslug5` (MAME 0.289, the set in `roms\`, written to
`analysis\phase2`). The scripted game: a coin at 2600, START at 2800, the game's "How to play",
Soldier Select from about 5700 (A at 6100: Marco), Mission 1 with the bot.

| Run (`ctest`) | Frames | RAM + palette (VBlank acks) | Images |
|---|---|---|---|
| `mslug5_attract_vs_mame` | 10 007 | 10 766 / 10 776, 10 known | 10 002 / 10 002 |
| `mslug5_start_vs_mame` | 9 001 | 8 777 / 8 798, 21 known | 8 996 / 8 996 |

`ctest`: **89/89** (84 Metal Slug 3 and X, 5 Metal Slug 5). The first boot has no watchdog
reset (MAME's reset notifier never fires; the boot check simply runs twice).

### Known differences (stack only, checked byte by byte)

- **`start`** (`start_known_vblank.txt`): VBlanks 2472-2473 and 2512-2530. Two VBlanks taken one
  instruction later by MAME (at 2472 the pushed PC is `0x16B98` in MAME, `0x16B96` in the port:
  `move.w -(a2),d0`), and the residue in the dead stack (`0x10F29B-0x10F2F3`) until it is
  overwritten. The documented Metal Slug 3 residue.
- **`attract`** (`attract_known_vblank.txt`): VBlanks 7604-7613. The 68000 cycles are identical
  instruction by instruction (`compare_cycles.py`: 258 692 instructions, 0 durations differ); at
  cycle 1 483 149 319 (frame 7316) MAME reads the LSPC line counter as `0x100` where the port reads
  `0xFF`, 1 cycle into line 263. Another read at exactly the same position (cycle 552 517 639)
  matches MAME, and moving the port's sampling point (5 cycles before the end instead of 6)
  breaks other reads: it is MAME's behaviour at the frame boundary, not a fixable model. The
  game's load meter takes the other branch at `0xF08`; the next 10 VBlanks are taken one
  instruction apart; RAM (stack only) and image converge.

## Audio: MAME's scheduler (deferred)

The port's audio differs from MAME's `-wavwrite` in both runs (correlation 0.97, 23.7 % of the
samples exact in the game run). What was measured (`analysis\phase2\ym`):

- **The Z80 writes the same thing:** all 12 246 port writes of the first 30 s (YM2610, reply) are
  identical in order and value (`tools/mame/trace_ym.lua` against `PD_TRACE_YM`). Only their time
  changes, by a few microseconds, after some of the 68000's commands.
- **The first change** (command `0x03` from the BIOS at 4.724 s): the Z80 waits for the NMI in a
  `JP 0xFFFD` loop (10 T). MAME's timing of every Z80 read (`tools/mame/trace_z80_reads.lua`)
  shows the 68000's write at T = 18 896 249.0 and the NMI vector fetched at T = 18 896 259, so the
  NMI was taken at the loop's boundary at T = 18 896 248, **before the write**: the trace logs the
  write before the Z80's reads at 238-245. The 68000 ran ahead within MAME's timeslice and the
  Z80, behind it, saw the NMI already asserted. The port, with the command exactly at its time,
  takes it at the next boundary (11 T later); the NMI handler then lasts the same in both (167 T).
- Over the 129 commands of the first 30 s, the command-to-NMI latency differs from MAME's by
  -2.7 to +2.1 microseconds, depending on where the Z80 is.
- The port's 68000 and Z80 cycles, the NMI model (pending command and NMI enable) and the handler
  are as MAME's; reproducing this needs a model of MAME's timeslices (when the Z80 is behind the
  68000), the same kind of problem as Metal Slug 3's raster interrupt residue.

### Option A (the user's choice): the rule learned as a black box, time-boxed

With MAME's Z80 timing per read around every command (`trace_z80_reads.lua`, `PD_AROUND`), three
separate effects were found. Each was tried on Metal Slug 5 and on all of Metal Slug 3's and Metal
Slug X's tests:

| Effect | Evidence | Metal Slug 5 | Metal Slug 3 / X | Kept |
|---|---|---|---|---|
| **An NMI does not interrupt an IRQ acknowledge**: MAME runs the handler's first instruction (DI at `0x0038`) first | two cases (20.598 s, 97.947 s): the NMI vector is fetched 4 T after the 0x0038 fetch in MAME, right after the acknowledge in the port | needed | all pass | **yes** (`sound.c`) |
| **The command a 68000 cycle earlier** (`write_end() - 4`, the start of the write access, instead of `- 3`) | the BIOS command at 4.724 s falls exactly on the end of a 10 T `JP` and MAME takes the NMI there | needed (otherwise 0.25 us offsets drift) | 22 audio tests fail (e.g. a command at 0.33 T into a 7 T instruction that MAME does not take early) | no |
| **The YM2610's extra sample at power-on** (instead of at the soft reset) | without it, every ADPCM-A sound of Metal Slug 5 starts one step (3 samples) early; with it, both runs are identical | needed | the reset's sample is needed for 3 audio tests (`mission4`, `start_mission_option`, `partida1`) | no |

With all three, **Metal Slug 5's two runs are identical to MAME sample for sample** (9 388 796 and
8 444 361 samples), and Metal Slug 3's tests fail. No single rule fits both games for the last
two effects. Both concern the alignment of the 68000, the Z80 and the YM2610 from power-on:
Metal Slug 3's paths were validated after its first-boot watchdog reset (it is silent before it),
Metal Slug X has no reset and its audio was never sample-exact, and Metal Slug 5 is the first game
that runs entirely on the power-on path. The time box ended there; per the user's instruction the
code keeps the first rule only (Metal Slug 3 and X unchanged: `ctest` 89/89), and Metal Slug 5's
audio stays different (64.6 % and 23.7 % exact samples, correlation 0.91 / 0.97; the Z80's
12 246 writes of the first 30 s identical in order and value).

## Tools

- `tools/make_reference.py`: the decrypted reference files and the `sm1.sm1` stand-in.
- `tools/bus_probe.py` + `tools/mame/bus_probe.lua`: black-box reads and writes on the 68000 bus.
- `tools/mame/trace_z80_nmi.lua`: times of the 68000's commands, the NMI vector fetches, the
  command reads and the replies; `tools/mame/trace_z80_reads.lua`: every Z80 read with its time
  (the debugger's Z80 trace gives no cycle counts).
- `tools/mame_run.py`: `--game mslug5` (default), the set from `roms\` (MAME's `-rompath`), the
  Metal Slug 5 menu steps.
- `tests/loader/link_set.py`: the test folder with only the MAME set.

## Pending

- The audio (deferred by the user, 2026-10-18): the power-on alignment of the 68000, Z80 and
  YM2610 (above). Starting point: the two Metal Slug 5-only corrections of the Option A table;
  Metal Slug 3's tests after its reset must keep passing, and Metal Slug X's audio is a second
  witness.
- A longer game (Phase 3's recordings) and the other missions (Phase 4).
