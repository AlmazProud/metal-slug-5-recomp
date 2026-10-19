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
