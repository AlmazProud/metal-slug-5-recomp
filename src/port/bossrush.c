/* Boss Rush (bossrush.h).
 *
 * The start bytes (game_profile.start_mission: mission, section) are watched through the RAM
 * write hook (ng_hook_word). The section byte is 0xFF while a section runs; the game writes the
 * next section there when one ends (the next mission's first section, or the mission's next
 * one) and the stage start routine reads it right after, in the same frame. So:
 *   - the first boss: the new game's start bytes are set like Mission mode's (cheats.c); its
 *     section runs when the game writes 0xFF over that boss's section;
 *   - when a boss section ends (any other value written over 0xFF), the next boss's mission and
 *     section are written at once in its place: the stage start loads it, with the score,
 *     lives, bombs and weapon carried over as between two missions;
 *   - after the last boss nothing is changed: the game's own ending follows.
 */
#include "bossrush.h"

#include "cheats.h"
#include "neogeo.h"
#include "profile.h"

enum { WAIT_FIRST, RUNNING, LOADING };
static int active, seg, defeated, phase, event;

int bossrush_supported(void) { return game_profile.n_rush > 0 && game_profile.start_mission && profile_supported(); }
int bossrush_active(void) { return active; }
int bossrush_defeated(void) { return defeated; }

int bossrush_total(void)
{
    int n = 0;
    for (int i = 0; i < game_profile.n_rush; i++) n += game_profile.rush[i].bosses;
    return n;
}

static void on_write(uint16_t before, uint16_t after)
{
    if (!active) return;
    int old_section = before & 0xFF, section = after & 0xFF;
    const ProfileRush *r = &game_profile.rush[seg];
    switch (phase) {
    case WAIT_FIRST:
        /* the first boss section runs: 0xFF written over its section (the soldier select writes
           the bytes too, with other values) */
        if (section == 0xFF && old_section == r->section && (after >> 8) == r->mission) phase = RUNNING;
        break;
    case LOADING:
        /* the next boss section runs: 0xFF written once it is loaded (within a mission the game
           may write its own next section again after ours was read) */
        if (section == 0xFF && (after >> 8) == r->mission) phase = RUNNING;
        break;
    case RUNNING:
        if (old_section != 0xFF || section == 0xFF) break;
        /* the boss section ended: the game asks for another section */
        defeated += r->bosses;
        if (seg + 1 >= game_profile.n_rush) {
            event = BR_CLEARED;
            active = 0;
            ng_hook_word = 0;
            break;
        }
        seg++;
        uint8_t *b = ng.ram + (game_profile.start_mission & 0xFFFF);
        b[0] = game_profile.rush[seg].mission;
        b[1] = game_profile.rush[seg].section;
        phase = LOADING;
        event = BR_NEXT;
        break;
    }
}

void bossrush_start(void)
{
    if (!bossrush_supported()) return;
    active = 1;
    seg = defeated = 0;
    phase = WAIT_FIRST;
    event = BR_NONE;
    ng_hook_word = game_profile.start_mission & 0xFFFFFE;
    ng_on_hook_write = on_write;
    cheats_start_mission_once = game_profile.rush[0].mission;
    cheats_start_section_once = game_profile.rush[0].section;
}

int bossrush_running(void) { return active && phase == RUNNING; }

void bossrush_stop(void)
{
    active = 0;
    ng_hook_word = 0;
    cheats_start_section_once = -1;
}

int bossrush_frame(void)
{
    int e = event;
    event = BR_NONE;
    return e;
}
