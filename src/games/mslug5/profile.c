/* Metal Slug 5: the frontend's game profile. It grows as the game's addresses are found and
 * verified against MAME (docs/PHASE4_PROFILE.md); the frontend only shows the options whose
 * addresses are here (menu.c). Addresses and hashes only, never game data.
 *
 * The program shares Metal Slug 3's engine: most routines are Metal Slug 3's, at other addresses
 * (`a5` is 0x108000 in the game code too).
 */
#include "profile.h"

static const int SOUND_COUNT = 0;

/* Weapons 0x00-0x12: the records at 0x1C298 (weapon, class, sub-type, -, initial ammo, ammo per
   extra pickup, announcer voice), Metal Slug 3's layout. 0-15 have Metal Slug 3's classes and ammo
   (names as there); 16-18 are not identified yet. */
static const char *const WEAPONS[] = {
    "Pistol", "Big blast (unused?)", "Shotgun", "Rocket Launcher", "Flame Shot",
    "Heavy Machine Gun", "Laser Shot", "Big Shotgun", "Big Rocket Launcher", "Big Flame Shot",
    "Big Heavy Machine Gun", "Big Laser Shot", "Enemy Chaser", "Iron Lizard", "Drop Shot",
    "Super Grenade", "Weapon 16", "Weapon 17", "Weapon 18",
};

/* Code that must be identical to the reference copy's for this profile to be used (profile.c). */
static const ProfileWindow WINDOWS[] = {
    {0x0008D0, 0x0008EA},     /* debug dips cleared on boot (0x8DE) */
    {0x000CB6, 0x000D4E},     /* VBlank handler: shadow load meter (dip 0x0010, 0xCC4 / 0xD36) */
    {0x000EF2, 0x000F1E},     /* VBlank wait loop (wait_start/wait_end), VBlanks per logic cycle */
    {0x002622, 0x00264A},     /* developer mode copied to 0x10F002 (0x2622); dips cleared without it */
    {0x003B40, 0x003B60},     /* developer mode check (0x3B4A) */
    {0x009086, 0x009136},     /* developer pause: SELECT + D (copy at $7002(a5)) */
    {0x00988A, 0x009B26},     /* "SET DEBUG DIP": names, item -> bit table (0x9A98), toggle (0x9AD4) */
    {0x0497A6, 0x0497B4},     /* BLOOD soft dip check (tst.b 0x10FD92) */
    {0x047578, 0x04758A},     /* new game: start mission set to 0 (0x47584 -> 0x4823A) */
    {0x0477E4, 0x047800},     /* mission controller: loads the mission to start at (0x477EE) */
    {0x0479B6, 0x0479C0},     /* section byte set to 0xFF once the mission runs (0x479BA) */
    {0x047E92, 0x047EAC},     /* next mission at the end of one (0x47E9A) */
    {0x04823A, 0x048262},     /* the start mission setter */
    {0x01BE84, 0x01BE96},     /* player tables: 0x10D450, 0x10D460 */
    {0x01C298, 0x01C454},     /* weapon records (0x1C298, 10 bytes), the give routine (0x1C356: D0
                                 player, D1 weapon) and its pickup: ammo +0xC, weapon +4, previous +5 */
    {0x04E854, 0x04E948},     /* status object: character $98, lives $99 (from the BIOS lives option) */
};

const GameProfile game_profile = {
    .title = "METAL SLUG 5",
    .subtitle = "",
    .windows = WINDOWS,
    .n_windows = (int)(sizeof WINDOWS / sizeof WINDOWS[0]),
    .windows_sha256 = "0594ad08e3d5d743ea416db33c7f70bc7ca2016fba51e54c2b802da3acab277e",
    .vehicles = NULL,
    .n_vehicles = 0,
    .sounds = NULL,
    .n_sounds = &SOUND_COUNT,

    /* Debug dips (word 0x10F000, cleared on boot at 0x8DE): only with the BIOS development mode
     * (0x10FE80, checked at 0x3B4A); the game copies the mode to 0x10F002 ($7002(a5), 0x2622) and
     * its pause code checks the copy. Forced for the cartridge's reads, as in Metal Slug 3. */
    .dips_word = 0x10F000,
    .devmode_word = 0x10FE80,
    .devmode_copy_word = 0x10F002,
    /* Bits from the developers' "SET DEBUG DIP" menu (names 0x988A-0x99E3, bit table 0x9A98,
     * toggle 0x9AD4): the same 15 switches and bits as Metal Slug 3's. */
    .dips = {
        .invincible = 0x8000,              /* MUTEKI */
        .infinite_bombs = 0x0004,          /* unlimited grenades */
        .infinite_ammo = 0x0008,           /* unlimited POW gun */
        .d_kills_all = 0x0001,             /* D button: every enemy dies */
        .boxes = 0x2000 | 0x4000 | 0x0080, /* VIEW ATTACK / BODY / PUSH RECT */
        .info = 0x0100,                    /* VIEW INFOMATION */
        .ground = 0x0800 | 0x1000,         /* VIEW GEO SCROLL A / B */
        .pa_point = 0x0002,                /* VIEW PA POINT */
        .pause_anytime = 0x0200,           /* ITSUDEMO PAUSE */
        /* No menu entry: the VBlank handler turns the shadow on (0x3A0011, 0xCD0) while it works
         * and off at the end (0x3A0001, 0xD42): the lines drawn meanwhile are darker. */
        .cpu_meter = 0x0010,
    },

    /* Developer menu: 0x9086 (developer mode copy $7002(a5) on) asks for the pause when the
     * player's SELECT is held (bits 1 / 3 of -$334C(a5) = 0x104CB4) and D is newly pressed
     * (bit 7 of -$3347(a5) / -$3341(a5) = 0x104CB9 / 0x104CBF), as in Metal Slug 3. */
    .dev_menu = DEV_MENU_SELECT_D,

    /* Blood: the US soft dips (header 0x2AC8) are Metal Slug 3's list (CONTINUE ... LANGUAGE,
     * BLOOD); the BIOS keeps them from 0x10FD8A, so BLOOD is 0x10FD92, read by 0x497A6. */
    .blood_word = 0x10FD92u,
    .blood_mask = 0xFF00u,

    /* Mission and section to start at: 0x10D680 / 0x10D681 ($5680(a5)). A new game sets both to 0
     * (0x47584, after the game's "How to play", which is mission 8); the mission controller loads
     * them at 0x477EE after the soldier select (scripted game: set at frame 5401, loaded at 6293).
     * Missions 0-4; 6 and 7 are the attract demos, 8 "How to play". */
    .start_mission = 0x10D680u,
    .missions = 5,
    /* Current mission: the mission controller's $7C (0x100B30 + 0x7C), written at the start of a
     * mission (0x477EE) and by the next-mission step at its end (0x47E9A). Player 1's score:
     * 0x10DE14, 8 BCD digits (as shown on the HUD). */
    .mission_now = 0x100BACu,
    .score_p1 = 0x10DE14u,

    /* Players. Tables 0x10D450 / 0x10D460 ($5450(a5)), a block of 0x10 bytes per player:
     * +2 shot counter, +3 sub-type, +4 weapon, +5 previous weapon, +6 grenade type, +7 bombs,
     * +0xC ammo (word, 0xFFFF = infinite). Player objects 0x100CB8 / 0x100DA8 ($8C: their table,
     * $78: player). Status objects 0x1009A8 / 0x100A6C: $98 character (internal: Marco 0, ...),
     * $99 lives. In game: BIOS player status 1 and the player object pointing to its table. */
    .player_table = 0x10D450u,
    .table_stride_byte = 0x10,
    .table_stride_word = 0x10,
    .table_shots = 2,
    .table_subtype = 3,
    .table_weapon = 4,
    .table_bombs = 7,
    .table_ammo = 0xC,
    .player1_object = 0x100CB8u,
    .player2_object = 0x100DA8u,
    .object_table_ptr = 0x8C,
    .player1_soldier = 0x100A40u,
    .player2_soldier = 0x100B04u,
    .soldier_internal = 1,
    .player1_lives = 0x100A41u,
    .player2_lives = 0x100B05u,
    /* Weapons: the cheat calls the game's own routine 0x1C356 (D0 player, D1 weapon), the one its
     * weapon items call (0xB4506): table, ammo, form and announcer as when picked up. Its pickup
     * keeps the previous weapon at +5 and clears the player object's $A1. */
    .weapons = sizeof WEAPONS / sizeof WEAPONS[0],
    .weapon_names = WEAPONS,
    .give_routine = 0x1C356u,
    .rom_weapon_subtype = 0x1C29Au,
    .rom_weapon_subtype_stride = 10,
    .rom_weapon_ammo = 0x1C29Cu,
    .rom_weapon_ammo_stride = 10,
    .object_pickup_flag = 0xA1,
    .table_previous_weapon = 5,

    /* Title screen logo (attract, from frame ~911 after power-on with empty SRAM): sprites 344-376
     * ("METAL SLUG" and the 5) and 380 ("TM", first tile 0x44855, used to recognize the moment);
     * the background is sprites 324-343, the SNK PLAYMORE logo 377-379. The title draws its
     * sprites every other frame. */
    .logo_first = 344,
    .logo_last = 376,
    .logo_tm = 380,
    .logo_tm_tile = 0x44855u,
    .logo_max_frames = 2000,
    /* Fast boot: the BIOS boot screen (no watchdog reset), black, and the game's first image (the
       parental advisory warning) at frame 301. */
    .boot_frames = 301,

    /* Main loop: waits at 0xEF2-0xEFA (cmp.b -$7FE9(a5),-$7FEA(a5): VBlanks since the last logic
     * cycle against the game's own threshold) and exits at 0xEFC, storing the count at
     * -$7FE6(a5) = 0x10001A. */
    .wait_start = 0x0EF2u,
    .wait_end = 0x0EFCu,
    .ram_frames_per_tick = 0x001Au,
};
