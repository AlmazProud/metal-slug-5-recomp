/* Metal Slug 5 (SNK Playmore, 2003): game descriptor (hashes, addresses and chip facts; never game
 * data).
 *
 * There is no PC release: the only copy is MAME's `mslug5` set (NGM-2680), which is encrypted
 * (NEO-PVC program, CMC50 sprites, fix and M1, PCM2 ADPCM; docs/ROM_MAP.md). Hashes from
 * `mame -listxml mslug5` (MAME 0.289). Until the runtime has the decryption, the set is recognized
 * and reported, not loaded (mame_encrypted), and the runtime loads the decrypted reference files.
 */
#include "neogeo.h"

static const NgMameFile MAME[] = {
    {NG_MAME_P, 0, "268-p1cr.p1", 4194304, 0xd0466792, "880819933d997fab398f91061e9dbccb959ae8a1", "arcade"},
    {NG_MAME_P, 1, "268-p2cr.p2", 4194304, 0xfbf6b61e, "9ec743d5988b5e3183f37f8edf45c72a8c0c893e", NULL},
    {NG_MAME_M, 0, "268-m1.m1", 524288, 0x4a5a6e0e, "df0f660f2465e1db7be5adfcaf5e88ad61a74a42", NULL},
    {NG_MAME_V, 0, "268-v1c.v1", 8388608, 0xae31d60c, "c42285cf4e52fea74247860813e826df5aa7600a", NULL},
    {NG_MAME_V, 1, "268-v2c.v2", 8388608, 0xc40613ed, "af889570304e2867d7dfea1e94e388c06249fb67", NULL},
    {NG_MAME_C, 0, "268-c1c.c1", 8388608, 0xab7c389a, "025a188de589500bf7637fa8e7a37ab24bf4312e", NULL},
    {NG_MAME_C, 1, "268-c2c.c2", 8388608, 0x3560881b, "493d218c92290b4770024d6ee2917c4022753b07", NULL},
    {NG_MAME_C, 2, "268-c3c.c3", 8388608, 0x3af955ea, "cf36b6ae9b0d12744b17cb7a928399214de894be", NULL},
    {NG_MAME_C, 3, "268-c4c.c4", 8388608, 0xc329c373, "5073d4079958a0ef5426885af2c9e3178f37d5e0", NULL},
    {NG_MAME_C, 4, "268-c5c.c5", 8388608, 0x959c8177, "889bda7c65d71172e7d89194d1269561888fe789", NULL},
    {NG_MAME_C, 5, "268-c6c.c6", 8388608, 0x010a831b, "aec140661e3ae35d264df416478ba15188544d91", NULL},
    {NG_MAME_C, 6, "268-c7c.c7", 8388608, 0x6d72a969, "968dd9a4d1209b770b9b85ea6532fa24d262a262", NULL},
    {NG_MAME_C, 7, "268-c8c.c8", 8388608, 0x551d720e, "ebf69e334fcaba0fda6fd432fd0970283a365d12", NULL},
};

static const NgGame GAME = {
    .id = "mslug5",
    .title = "Metal Slug 5",
    .project = "metal-slug-5-recomp",
    .gog_id = "",                       /* no PC release */
    /* The decrypted reference files (tools/make_reference.py: MAME's regions from the set above,
       in the runtime's DotEmu layout), until the runtime decrypts the set itself (Phase 5). */
    .dotemu = {
        [NG_DOTEMU_P] = {"mslug5_game_m68k", 8388608, "60671bbe51782d5ae7379cb7a65b06b2c22fafbf6109579c6e664d33a6d48da0"},
        [NG_DOTEMU_BIOS] = {"mslug5_bios_m68k", 131072, "01ff1db85c5b209d4f5879ea8348e3b39a237532c37232f14c2b48945e9aa7d8"},
        [NG_DOTEMU_FIX_GAME] = {"mslug5_game_sfix", 131072, "bac0f26fb13b718d6a4787be48a1fce5c08b6b9cdc52a5487a95435fcd81067b"},
        [NG_DOTEMU_FIX_BIOS] = {"mslug5_bios_sfix", 131072, "676765a530d9dcd2a5161aeefa1f91e7fbae273dbaa9b1cd68f5adbc71bb55b6"},
        [NG_DOTEMU_TILES] = {"mslug5_tiles", 67108864, "8e910cb7d32d1060c1421d60e72d7f5b98b90d713ec3122139b4e94db89bdab9"},
        [NG_DOTEMU_ZOOM] = {"mslug5_zoom_table", 131072, "2a76f023dc578804c6bcd58ed514ffc04fcb433b3bd75d4452575ffda57a0707"},
        [NG_DOTEMU_Z80] = {"mslug5_game_z80", 524288, "df8bf6e4db78a7a1f7ff7455d42002757887e50300ec67acb8c5764eb763f3fb"},
        [NG_DOTEMU_ADPCM] = {"mslug5_adpcm", 16777216, "860f1106a8324acb72284292ec0fd2fdce2b256fa943e15baf6e5979a14be9d2"},
    },
    .mame = MAME,
    .n_mame = (int)(sizeof MAME / sizeof MAME[0]),
    .crypt = NULL,
    .mame_encrypted = 1,
    .cart = NG_CART_PVC,
    .fix_bank = NG_FIX_BANK_NONE,
};

const NgGame *const ng_game = &GAME;
