/* Metal Slug 5: the frontend's game profile. Empty for now: the cheats, debug options, red blood,
 * title logo, boss bar and Boss Rush stay off (n_windows == 0) until the game's addresses are
 * found and verified against MAME (Phase 4).
 */
#include "profile.h"

static const int SOUND_COUNT = 0;

const GameProfile game_profile = {
    .title = "METAL SLUG 5",
    .subtitle = "",
    .windows = NULL,
    .n_windows = 0,
    .windows_sha256 = "",
    .vehicles = NULL,
    .n_vehicles = 0,
    .sounds = NULL,
    .n_sounds = &SOUND_COUNT,
};
