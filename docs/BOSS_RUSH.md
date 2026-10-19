# Boss health bar and Boss Rush (Metal Slug 5)

Metal Slug 3's quality-of-life features, for Metal Slug 5 (asked for by the user as a stage of
its own within Phase 4). Worked in stages, each one closed with a report, as in Metal Slug 3:

| Stage | Content | Status |
|---|---|---|
| 0 | How to reach every boss without playing the whole game | **Done** (2026-10-18), waiting for approval |
| 1 | Identify the bosses (code, life, death) | Pending |
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

### Open for stage 1

- `BOSS A` and `BOSS B` (Mission 5): what they are (the stairs' soldiers may be the fight itself)
  and a way through for the bot (the stairs, the gap).
