/* Metal Slug 5: the frontend's game profile. It grows as the game's addresses are found and
 * verified against MAME (docs/PHASE4_PROFILE.md); the frontend only shows the options whose
 * addresses are here (menu.c). Addresses and hashes only, never game data.
 *
 * The program shares Metal Slug 3's engine: most routines are Metal Slug 3's, at other addresses
 * (`a5` is 0x108000 in the game code too).
 */
#include "profile.h"

static const int SOUND_COUNT = 0;

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
};

const GameProfile game_profile = {
    .title = "METAL SLUG 5",
    .subtitle = "",
    .windows = WINDOWS,
    .n_windows = (int)(sizeof WINDOWS / sizeof WINDOWS[0]),
    .windows_sha256 = "1889ee4875346df5247abd23a0a0d08ee3229ad747cff04eb19ef2468b78e233",
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

    /* Main loop: waits at 0xEF2-0xEFA (cmp.b -$7FE9(a5),-$7FEA(a5): VBlanks since the last logic
     * cycle against the game's own threshold) and exits at 0xEFC, storing the count at
     * -$7FE6(a5) = 0x10001A. */
    .wait_start = 0x0EF2u,
    .wait_end = 0x0EFCu,
    .ram_frames_per_tick = 0x001Au,
};
