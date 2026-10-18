/* Boss Rush (docs/BOSS_RUSH.md, stage 3): every boss in a row, in one game.
 *
 * The game starts at the first boss's section (the start mission and section bytes, as Mission
 * mode does). When a boss falls the game goes on to its next section by itself; while Boss Rush
 * runs, the stage start routine (game_profile.stage_start_*) reads the next boss's mission and
 * section instead (a forced read, only there): the score, lives, bombs and weapon carry over as
 * between two missions. After the last boss the game's own ending follows.
 */
#ifndef BOSSRUSH_H
#define BOSSRUSH_H

enum { BR_NONE, BR_NEXT, BR_CLEARED };

int bossrush_supported(void);
int bossrush_total(void);                /* bosses in the run */
void bossrush_start(void);               /* before the new game's coin and START */
void bossrush_stop(void);
int bossrush_active(void);
/* After every emulated frame: BR_NEXT when a boss section ended (the next one loads),
   BR_CLEARED after the last one. */
int bossrush_frame(void);
int bossrush_defeated(void);             /* bosses defeated so far */
int bossrush_running(void);              /* a boss section is loaded and running */

#endif
