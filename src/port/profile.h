/* Game profile for the frontend: the per-game data the cheats, the debug options, the red blood
 * option, the title logo and the sound menu rely on (addresses in the game's program and RAM,
 * sound names). Each executable links its game's profile (src/games/<id>_profile.c), which
 * defines `game_profile`. A game without a profile (n_windows == 0) has those options off.
 */
#ifndef PROFILE_H
#define PROFILE_H

#include <stdint.h>

typedef struct { uint32_t first, last; } ProfileWindow;
typedef struct { int type; const char *name; } CheatVehicle;
typedef struct { int form; const char *name; } CheatForm;
/* Boss Rush: a boss section (the start mission and section bytes) and the bosses in it. */
typedef struct { uint8_t mission, section, bosses; } ProfileRush;
/* A boss's code (its object's routine, +0, is between code_lo and code_hi), its full life and its
   name (shown on the health bar). */
typedef struct { uint32_t code_lo, code_hi; int life; const char *name; } ProfileBoss;
enum { DEV_MENU_SELECT_D = 1, DEV_MENU_D_SELECT = 2 };

/* Sound driver commands: driver mode (00 music, 10 effects, 11 voices), command, duration in
 * tenths of a second (0xFFFF = looping) and name. */
typedef struct {
    uint8_t mode, command;
    uint16_t tenths;
    const char *name;
} Sound;

/* Gamepad rumble of an effect (driver mode 10): big motor, small motor, milliseconds. */
typedef struct { uint8_t command; uint16_t low, high, ms; } SoundRumble;

/* Debug dips (bits of the word at dips_word) behind the frontend's switches; 0 = the game has
   none. The names are the developers' own "SET DEBUG DIP" menu, in the game's program. */
typedef struct {
    uint16_t invincible, infinite_bombs, infinite_ammo, d_kills_all;
    uint16_t boxes, info, ground, cpu_meter, pa_point, pause_anytime;
} ProfileDips;

typedef struct {
    const char *title;                  /* start menu title, uppercase */
    const char *subtitle;
    /* Program windows (68000 view) that must match `windows_sha256` for the addresses below to
       be used: one SHA-256 over all of them, in order. */
    const ProfileWindow *windows;
    int n_windows;
    const char *windows_sha256;
    const CheatVehicle *vehicles;       /* object types that the vehicle cheat spawns */
    int n_vehicles;
    const Sound *sounds;                /* built-in sound names */
    const int *n_sounds;
    const SoundRumble *rumble;          /* rumble of the identified effects */
    int n_rumble;
    /* Addresses and values (see the game's profile file for what each one is). */
    uint32_t wait_start;
    uint32_t wait_end;
    uint32_t ram_frames_per_tick;
    uint32_t dips_word;
    uint32_t devmode_word;
    uint32_t devmode_copy_word;
    uint32_t game_state;
    uint32_t game_state_playing;
    uint32_t player_table;
    uint32_t player1_object;
    uint32_t player2_object;
    uint32_t object_character;
    uint32_t object_form;
    uint32_t fat_food;
    uint32_t stage_word;
    uint32_t fat_check_first;
    uint32_t fat_check_last;
    uint32_t fat_stage;
    uint32_t spawn_routine;
    uint32_t spawn_parent;
    uint32_t spawn_x;
    uint32_t spawn_y;
    uint32_t player1_soldier;
    uint32_t player2_soldier;
    uint32_t player1_lives;
    uint32_t player2_lives;
    uint32_t rom_weapon_subtype;
    uint32_t rom_weapon_ammo;
    uint32_t rom_weapon_flag;
    uint32_t blood_word;
    uint32_t blood_mask;
    uint32_t logo_first;
    uint32_t logo_last;
    uint32_t logo_tm;
    uint32_t logo_tm_tile;
    uint32_t logo_max_frames;
    /* Fast boot: frames from power-on to the game's first image (the BIOS boot before it). */
    uint32_t boot_frames;
    /* Start mission: the game keeps the mission and the section to start at in two bytes
       (start_mission, start_mission + 1); a new game sets both to 0 and loads the mission a moment
       later. missions = 0: not supported. */
    uint32_t start_mission;
    uint32_t missions;
    /* Mission and Arcade modes (progress.c, window.c): the current mission byte (0-based; the
       game's "next mission" step makes it n + 1) and player 1's score (4 bytes, BCD). */
    uint32_t mission_now;
    uint32_t score_p1;
    ProfileDips dips;
    /* Player table layout: a field is at player_table + offset + player * stride. Metal Slug X
       interleaves both players (stride 1 for bytes, 2 for words); Metal Slug 3 has a block per
       player. */
    uint32_t table_stride_byte, table_stride_word;
    uint32_t table_shots, table_subtype, table_weapon, table_bombs, table_ammo;
    /* Weapons: count, names (English) and the ROM tables the game's pickup routine reads, with
       their strides (rom_weapon_flag = 0: the pickup clears the player object's flag). */
    uint32_t weapons;
    const char *const *weapon_names;
    uint32_t rom_weapon_subtype_stride, rom_weapon_ammo_stride;
    /* Soldier: 1 if player*_soldier holds only the internal character (Marco 0, Tarma 1, Eri 2,
       Fio 3), used from the next life; 0 (Metal Slug X): the soldier select index, with the
       internal character in the byte before it and in the player object. */
    int soldier_internal;
    /* In game without game_state: BIOS player status (0x10FDB6 + player) = 1 and the player
       object's pointer at object_table_ptr pointing to its table. */
    uint32_t object_table_ptr;
    /* The developers' menu (cheats_dev_menu), with the developer mode on: a combination pressed
       twice, the first one pauses. DEV_MENU_SELECT_D: SELECT held, D pressed (Metal Slug X);
       DEV_MENU_D_SELECT: D held, SELECT pressed (Metal Slug 3); 0: not verified. */
    int dev_menu;
    /* Transformations the form cheat offers (forms[0]: normal, whose form depends on the weapon:
       rom_weapon_form, a byte per weapon), the food counter (player table word) that keeps the
       fat form, and the help line (English). */
    const CheatForm *forms;
    int n_forms;
    uint32_t rom_weapon_form;
    uint32_t table_food;
    const char *form_help;
    /* 1: from a form other than normal and fat the cheat goes back to normal first (the only
       change the game itself makes from them). */
    int form_normal_first;
    /* Spawn record (cheats.c): its first 4 bytes (command, length 10, group, flags) and where the
       type, x and y words go. */
    uint8_t spawn_head[4];
    uint8_t spawn_type_at, spawn_x_at, spawn_y_at;
    /* 0: spawn_x / spawn_y are the record's x and y. Otherwise the address of the scroll layer's
       screen position (two longs, 16.16) the record's x and y are relative to: the object then
       appears at spawn_x / spawn_y from player 1 (its object's screen position, longs at +0x3C
       and +0x40). */
    uint32_t spawn_layer;
    /* Weapon items: the stage object type of the items (0: the weapon cheat gives the weapon
       directly), its x offset from player 1 and the item kind of each weapon (0: none, the weapon
       is given directly). */
    uint32_t item_type, item_x;
    const uint8_t *weapon_items;
    /* Boss health bar (bossbar.c): the object list's head (links at +4, parent at +0xC), each
       object's life word and dead byte (bit 7) offsets, and the code of the known bosses (an
       object whose routine is there is labelled BOSS). object_list = 0: no bar. */
    uint32_t object_list;
    uint16_t object_life, object_dead;
    const ProfileBoss *bosses;
    int n_bosses;
    /* Boss Rush (bossrush.c): the boss sections in order, and the stage start routine that reads
       the start bytes (start_mission, start_mission + 1). n_rush = 0: no Boss Rush. */
    const ProfileRush *rush;
    int n_rush;
    int rush_weapon;          /* weapon whose item appears in front of the player at the start (0: none) */
    uint32_t stage_start_first, stage_start_last;
} GameProfile;

extern const GameProfile game_profile;

/* profile.c: 1 if the loaded program has the reference copy's code in every profile window
 * (the cheats, debug options and red blood are only offered then). */
int profile_supported(void);

#endif
