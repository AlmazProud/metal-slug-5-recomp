# Boss health bar and Boss Rush (Metal Slug 5)

Metal Slug 3's quality-of-life features, for Metal Slug 5 (asked for by the user as a stage of
its own within Phase 4). Worked in stages, each one closed with a report, as in Metal Slug 3:

| Stage | Content | Status |
|---|---|---|
| 0 | How to reach every boss without playing the whole game | **Closed** (2026-10-18) |
| 1 | Identify the bosses (code, life, death) | **Done** (2026-10-18), waiting for approval |
| 2 | Boss health bar | Pending |
| 3 | Boss Rush | Pending |

## Stage 0: the developer stage table

As in Metal Slug 3, the game starts a mission at a section of the developers' stage table, read
by the stage start (`0x477E4`): the mission byte `0x10D680` picks the group (`0x474E2`, a table
of 19 pointers at `0x474F4`) and the byte `0x10D681` the record within it (0-based). Writing both
during the soldier select (frame 5800 of the scripted start, `PD_POKE`) starts the game there; no
developer mode is needed. The records have Metal Slug 3's format:

`[length: word] [2 bytes] [routine: long] [data: long] [word] [area: word] [start X: word]
[name: text with \ch / \ck switches]`

The developers numbered the stages in another order than the final missions: the group of mission
byte 0 (Mission 1, the jungle) is named `3_x`, Mission 2's `4_x`, Mission 3's `1_x`, Mission 4's
`2_x`, Mission 5's `5_x`. Groups 5-8 are the ending (`MISSION ALL OVER`, `STAFF ROLL`, `GAME
END`), the attract demos and the "How to play" (mission byte 8); 0x10-0x12 three more.

### The boss sections (checked in the port: started there, invincible, a bot, screenshots)

| Mission | Mission byte | Record | Name in the table | What loads |
|---|---|---|---|---|
| 1 | 0 | 8 | `3_9 BOSS 3` | the jungle clearing, the red tank boss |
| 2 | 1 | 5 | `4_5 BOSS 4` | the sky, the airship boss |
| 3 | 2 | 6 | `1_6 BOSS1` | the factory room, the cannon machine boss |
| 4 | 3 | 3 | `2_4 BOSS 2-1` (records 3 and 4 are the same) | the desert, the sand worm / land submarine boss |
| 5 | 4 | 3 | `5_4 ... BOSS` | the ruined city: a mech boss comes |
| 5 | 4 | 4 | `5_5 BOSS A` | the stairs: hooded soldiers keep coming; the bot gets stuck there |
| 5 | 4 | 5 | `5_6 BOSS B` | the stone pillars: a boss's head appears; the bot falls into the gap, even invincible |
| 5 | 4 | 6 | `5_7 LAST BOSS` | the dark sky with the skull: the final boss |

Records 7 and 8 of Mission 5 (`5_T`, `5_E`) are records 3 and 5's sections started at
X `0x0580`, closer to the boss.

Script: `analysis\boss_rush\stage0` (outside the repo): `PD_DIPS=8000 PD_DEVMODE=1
PD_POKE=5800,10D680,<mission>;5800,10D681,<record>` with the scripted start.

### Objects' life and death

The damage routine `0x4AD18` is Metal Slug 3's `0x1A8B8` with other offsets: **the life is the
word at `+0x54`, the dead bit is bit 7 of `+0x61`**. The objects' list is headed at `0x100BF4`
(the stage's object root). Stage 1 identifies the bosses with these.

## Stage 1: the bosses

Found with `analysis\boss_rush\stage1\survey.py` (a section started as above, invincible, RAM
every 120 VBlanks, the objects with a life of 1000 or more) and `death.py` (the same with the "D
kills every enemy" dip, D pressed every 100 frames: the boss's routine, life and dead bit, the
mission and section bytes every 30 VBlanks).

| Boss | Life | Object | Code (alive -> defeat) | Section ends |
|---|---|---|---|---|
| Mission 1: the red tank | 5000 | top level; a part (`0xD35CE`) copies its life | `0x59ED6`-`0x5A4D6` -> `0x5A880`-`0x5A9AE` | mission 0 -> 1 |
| Mission 2: the airship | 10000 | top level | `0x5E0C0` -> `0x60982`-`0x60A6E` | mission 1 -> 2 |
| Mission 3: the cannon machine | 4000 | top level | `0x5327A`-`0x53938`, defeat `0x52F4A` | mission 2 -> 3 |
| Mission 4: the sand worm / land submarine | 7000 | top level | `0x55D10`-`0x5661E` | mission 3 -> 4 |
| Mission 5: `BOSS B` (the stone machine) | 2000 x 2 | two parts (`0xEE8EC`) of a controller | - | not seen |
| Mission 5: the final boss | 5000 | top level | `0x50D3C`-`0x51442` | mission 4 -> 5, then the ending (group 5) |

- **A boss section ends** when the game loads another one: the mission byte changes (Missions 1-4
  and the final boss), as in Metal Slug 3.
- **Not identified (time-boxed):** Mission 5's `5_4 ... BOSS` (record 3: a mech in the ruins, no
  object with 300 or more life in the bot's runs) and `BOSS A` (record 4: the stairs, none either;
  the bot never gets past the hooded soldiers). `BOSS B`'s parts never took damage: the bot falls
  into the gap between the pillars (even invincible) before reaching them, also with their life
  set to 1.

**Against MAME** (`analysis\boss_rush\stage1\boss_m1`-`m5`: the scripted start with the two
bytes written at frame 5800, invincible with the developer mode, `PD_DIPS=8000 PD_DEVMODE=1`):
images identical (one frame of Mission 1's run, 8576, drawn while an interrupt residue lasts);
RAM differs only in the listed VBlanks, checked byte by byte: the stack (`0x10F200`-`0x10F2FF`) and
single timing-derived words that are equal again one or two VBlanks later (`0x100018`, the line
measured after the wait loop; bytes the interrupted routine was writing). Tests
`mslug5_boss_m1_vs_mame` ... `_m5_vs_mame`.
