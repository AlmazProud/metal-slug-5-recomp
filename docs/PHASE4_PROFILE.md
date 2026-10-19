# Phase 4: Metal Slug 5's profile and frontend

**State:** in progress (started 2026-10-18).

Goal: the Metal Slug 3 port's frontend options working with Metal Slug 5 and verified against
MAME (the game profile `src/games/mslug5/profile.c`; the frontend only offers what the profile
supports).

## Plan

1. The game's RAM addresses, found in the program (`analysis\listing_p1.txt`) and checked in
   MAME: the VBlank wait loop, the mission and section, the start mission bytes, the player
   tables (weapon, ammo, bombs), the soldier and the lives.
2. Developer mode (BIOS `0x10FE80` and the game's copy) and the debug dips, with the developers'
   own menu if the program has one.
3. Cheats and the "Start mission" option, each with a MAME run that writes the same bytes at the
   same moments (`PD_POKE`), plus red blood (the soft dip) and the title logo.
4. The sound catalog (`tools/sound_catalog.py`), rumble and the frontend's texts (English and
   Spanish).
5. A MAME run per mission and its test.

The audio stays out of the pass criteria (deferred by the user, Phase 2).

## The engine

Metal Slug 5's program shares Metal Slug 3's engine: most routines the Metal Slug 3 profile
relies on are in Metal Slug 5 with the same code at other addresses (found by matching Metal
Slug 3's profile windows byte by byte, then checked one by one). `a5` is `0x108000` in the game
code too. The differences found so far: the player table is 0x10 bytes per player with other
offsets, the player object's fields moved (`$8C` table, `$78` player, `$A1` cleared on pickup),
objects store a pointer to their stage record, and the transformations use other fields and
tables.

## Addresses

| What | Address | Notes |
|---|---|---|
| VBlank wait loop | `0xEF2`-`0xEFA`, exit `0xEFC` | `cmp.b -$7FE9(a5),-$7FEA(a5)`: the game's own threshold (`0x100017`), not a fixed 2 |
| VBlanks per logic cycle | `0x10001A` | stored on leaving the wait loop |
| Debug dips | `0x10F000`-`0x10F001` | cleared on boot at `0x8DE` (and at `0x262E` without the developer mode) |
| Developer mode (BIOS) / the game's copy | `0x10FE80` / `0x10F002` | checked at `0x3B4A`; copied at `0x2622` |
| Developer pause and menu | `0x9086`; menu names `0x988A`, item -> bit table `0x9A98`, toggle `0x9AD4` | SELECT held + D newly pressed, twice, as in Metal Slug 3 |
| Load meter | `0xCC4` / `0xD36` | dip `0x0010`: shadow on (`0x3A0011`) while the VBlank handler works |
| Blood soft dip | `0x10FD92`, read at `0x497A6` | the US soft dips (`0x2AC8`) are Metal Slug 3's list |
| Mission / section to start | `0x10D680` / `0x10D681` | setter `0x4823A`; a new game sets 0 at `0x47584` |
| Current mission / section | `0x100BAC` / `0x100BAD` | the mission controller's `$7C` / `$7D` (`0x477EE`); next mission `0x47E9A` |
| Player 1's score | `0x10DE14` | 8 BCD digits (checked on the HUD) |
| Player tables (P1 / P2) | `0x10D450` / `0x10D460` | +2 shots, +3 sub-type, +4 weapon, +5 previous weapon, +6 grenade type, +7 bombs, +0xC ammo |
| Player objects | `0x100CB8` / `0x100DA8` | `$8C` their table |
| Status objects | `0x1009A8` / `0x100A6C` | `$98` character (Marco 0, Tarma 1, Eri 2, Fio 3), `$99` lives |
| Weapon records | `0x1C298` | 19 x 10 bytes, Metal Slug 3's layout |
| Give a weapon | `0x1C356` | D0 player, D1 weapon: what the weapon items call (`0xB4506`) |
| Stage object records | `0xE951C` | command 8 as Metal Slug 3's; type table `0xE8CC0`, list `0x100BF4` |

Missions 0-4; 6 and 7 are the attract demos, 8 the game's "How to play".

## Verified against MAME

All with images identical on every frame; RAM differs only in the VBlanks listed in each run's
`<run>_known_vblank.txt`, checked byte by byte (VBlank interrupts taken one instruction apart and
their stack residue, a transient byte, or MAME's boot, which is not deterministic: a replay of
the same run matches the port there).

| Run (`analysis\phase4`) | What |
|---|---|
| `debug/devmode` | developer mode |
| `debug/devdips` | developer mode and every debug dip of the menu (`FB8F`): RAM identical too |
| `debug/loadmeter` | the load meter dip |
| `debug/blood` | red blood |
| `debug/devmenu` | the developers' menu opened in Mission 1; the cheat's presses equal the script's |
| `missions/mission2`-`mission5` | the scripted game started at Missions 2-5 (`PD_POKE` during the soldier select) |
| `missions/mission4` + `PD_START_MISSION=4` | the "Start mission" option (`mslug5_start_mission_option_vs_mame`) |
| `cheats/cheats` | Heavy Machine Gun and Enemy Chaser through the game's routine, 63 bombs, 7 lives, Eri |
| `vehicles/vehicles` | the Metal Slug spawned in front of player 1 (ridden by the bot) |
| `forms/forms` | fat at frame 6700 (the food counter kept at 0x780), normal at 6900 |

Also in the port: the sound menu in the middle of the user's game (`mslug5_sound_menu`), the
title logo generated from the attract title (sprites 344-376 and the TM 380), fast boot to the
game's first image (frame 301).

## Sound driver

Every sound is a mode command and a command. Music is ADPCM-B in modes `07` (`21`-`50`) and `19`
(`D0`-`E0`), effects and voices ADPCM-A in `1A` (`20`-`DF`) and `18` (`19`-`E5`); the catalog
(`tools/sound_catalog.py ... mslug5`, `src/games/mslug5/sounds.c`) has 440 sounds. `03` silences
the driver but leaves the ADPCM-A sounds off until `07 20`, `08 20` and `0A A0` (what the game's
boot sends after it): that is the sound menu's silence sequence. The sound menu takes the modes
and the silence sequence from the game profile (Metal Slug X and 3 keep theirs).

- **Names:** only the weapons' announcer voices, from the weapon records (`18 C3`-`D9`). Metal
  Slug 5's samples are new recordings: none matches a named Metal Slug 3 sound (correlation of
  the catalog audio below 0.95; the Heavy Machine Gun voice lasts 1.3 s against 1.9 s), so the
  rest keep their numbers.
- **Rumble:** no automatic table (no effect identified); the user can set it per sound.

## Fat

The fat form exists, as in Metal Slug 3 (found by the user while testing; first discarded here
because the requested forms were looked at too early). Player object `$9F` current form, `$A0`
requested, `$9E` its class (table `0x1C1D8`); the request routine `0x1C1F4` reads the table
`0x1C238` by event x weapon class (`0x1C1C4`) x form class. Food (`0x1C8A4`) adds `0x1F0` to the
player table's +8 and at `0x780` asks for event 1: fat (form 3, or 4 with a weapon of class 2);
while fat the counter runs down (`0x202BA`) and event 2 brings him back. The cheat requests the
form the game's table gives (shared code: `form_table`, `form_weapon_class`, `form_class`,
`fat_class` in the profile; Metal Slug X and 3 unchanged) and logs its RAM writes for the MAME run.

## Not offered for Metal Slug 5

- **Other transformations:** forms 5-8 (events 3 and 4 of the form table) were not identified;
  10 and 11 hang the game. The form cheat offers normal and fat.
- **Weapons 16-18:** given with 200, 30 and 300 shots; not identified yet, listed by number.

Each option was also checked to have an effect: without it, the run differs from MAME's.

## Changes to shared code (Metal Slug 3 and X unchanged)

- **Weapon cheat:** with `give_routine`, the cheat calls the game's own routine while it waits
  for the VBlank (its RAM changes logged by `PD_SPAWN_POKES` for the MAME run, as the spawns');
  `object_pickup_flag` and `table_previous_weapon` for games that give the weapon directly.
- **Title logo:** after the wait, the capture takes the first frame that draws both the logo and
  the TM (Metal Slug 5's title draws its sprites every other frame).

## Pending

- Boss health bar and Boss Rush (Metal Slug 3's later options, a stage of their own there).
