/* Metal Slug 3 (SNK, 2000): game descriptor (hashes, addresses and chip tables; never game data).
 *
 * The GOG copy is the arcade `mslug3` set (NEO-SMA "green") with MAME's regions already
 * decrypted: docs/ROM_MAP.md. Its hashes are the reference for "verified". MAME sets of this
 * game are encrypted (NEO-SMA program, CMC42 sprites and fix): crypt.c decrypts them. Hashes from
 * `mame -listxml mslug3` (MAME 0.289).
 */
#include "neogeo.h"

/* NEO-SMA bank table: index (bits 3, 6, 9, 12, 14, 15 of the value written to 0x2FFFE4) ->
 * offset of the 1 MB window from the start of P2. Learned from MAME by writing all 65 536
 * values and sampling the window (tools/mame/sma_bank_map.lua, tools/sma_banks.py). */
static const uint32_t SMA_BANKS[64] = {
    0x000000, 0x1A0000, 0x0E0000, 0x260000, 0x320000, 0x4C0000, 0x400000, 0x000000,
    0x040000, 0x1E0000, 0x120000, 0x2A0000, 0x360000, 0x000000, 0x440000, 0x000000,
    0x020000, 0x1B0000, 0x0F0000, 0x270000, 0x330000, 0x000000, 0x410000, 0x000000,
    0x060000, 0x1F0000, 0x130000, 0x2B0000, 0x370000, 0x000000, 0x450000, 0x000000,
    0x070000, 0x200000, 0x140000, 0x2C0000, 0x380000, 0x000000, 0x460000, 0x000000,
    0x0B0000, 0x240000, 0x180000, 0x300000, 0x3C0000, 0x000000, 0x4A0000, 0x000000,
    0x090000, 0x210000, 0x150000, 0x2D0000, 0x390000, 0x000000, 0x470000, 0x000000,
    0x0D0000, 0x250000, 0x190000, 0x310000, 0x3D0000, 0x000000, 0x4B0000, 0x000000,
};

static const NgMameFile MAME[] = {
    {NG_MAME_X, 0, "green.neo-sma", 262144, 0x9cd55736, "d6efb2b313127c2911d47d9324626b3f1e7c6ccb", NULL},
    {NG_MAME_P, 0, "256-pg1.p1", 4194304, 0xb07edfd5, "dcbd9e500bfae98d754e55cdbbbbf9401013f8ee", NULL},
    {NG_MAME_P, 1, "256-pg2.p2", 4194304, 0x6097c26b, "248ec29d21216f29dc6f5f3f0e1ad1601b3501b6", NULL},
    {NG_MAME_M, 0, "256-m1.m1", 524288, 0xeaeec116, "54419dbb21edc8c4b37eaac2e7ad9496d2de037a", NULL},
    {NG_MAME_V, 0, "256-v1.v1", 4194304, 0xf2690241, "fd56babc1934d10e0d27c32f032f9edda7ca8ce9", NULL},
    {NG_MAME_V, 1, "256-v2.v2", 4194304, 0x7e2a10bd, "0d587fb9f64cba0315ce2d8a03e2b8fe34936dff", NULL},
    {NG_MAME_V, 2, "256-v3.v3", 4194304, 0x0eaec17c, "c3ed613cc6993edd6fc0d62a90bcd85de8e21915", NULL},
    {NG_MAME_V, 3, "256-v4.v4", 4194304, 0x9b4b22d4, "9764fbf8453e52f80aa97a46fb9cf5937ef15a31", NULL},
    {NG_MAME_C, 0, "256-c1.c1", 8388608, 0x5a79c34e, "b8aa51fa50935cae62ab3d125b723ab888691e60", NULL},
    {NG_MAME_C, 1, "256-c2.c2", 8388608, 0x944c362c, "3843ab300f956280475469caee70135658f67089", NULL},
    {NG_MAME_C, 2, "256-c3.c3", 8388608, 0x6e69d36f, "94e8cf42e999114b4bd8b30e0aa2f365578c4c9a", NULL},
    {NG_MAME_C, 3, "256-c4.c4", 8388608, 0xb755b4eb, "804700a0966a48f130c434ede3f970792ea74fa5", NULL},
    {NG_MAME_C, 4, "256-c5.c5", 8388608, 0x7aacab47, "312c1c9846175fe1a3cad51d5ae230cf674fc93d", NULL},
    {NG_MAME_C, 5, "256-c6.c6", 8388608, 0xc698fd5d, "16818883b06849ba2f8d61bdd5e21aaf99bd8408", NULL},
    {NG_MAME_C, 6, "256-c7.c7", 8388608, 0xcfceddd2, "7def666adf8bd1703f40c61f182fc040b6362dc9", NULL},
    {NG_MAME_C, 7, "256-c8.c8", 8388608, 0x4d9be34c, "a737bdfa2b815aea7067e7af2636e83a9409c414", NULL},
};

extern const NgMameCrypt MSLUG3_CRYPT;     /* crypt.c */

static const NgGame GAME = {
    .id = "mslug3",
    .title = "Metal Slug 3",
    .project = "metal-slug-3-recomp",
    .gog_id = "1370911530",
    .dotemu = {
        [NG_DOTEMU_P] = {"mslug3_game_m68k", 9437184, "30d0e23e20f9430f9cfdddf18feafefb485b7fc6ee82f4b9fe871e1e3f1eaad7"},
        [NG_DOTEMU_BIOS] = {"mslug3_bios_m68k", 131072, "01ff1db85c5b209d4f5879ea8348e3b39a237532c37232f14c2b48945e9aa7d8"},
        [NG_DOTEMU_FIX_GAME] = {"mslug3_game_sfix", 524288, "4c94163ccee4440165fffbc7c0b0ac0f5edff3d8744c05ea689b006dbb2a5e16"},
        [NG_DOTEMU_FIX_BIOS] = {"mslug3_bios_sfix", 131072, "676765a530d9dcd2a5161aeefa1f91e7fbae273dbaa9b1cd68f5adbc71bb55b6"},
        [NG_DOTEMU_TILES] = {"mslug3_tiles", 67108864, "0defc28d361448907c34334ed1d63bb7ac24dabc40e7d289397ad40eb4193c1a"},
        [NG_DOTEMU_ZOOM] = {"mslug3_zoom_table", 131072, "2a76f023dc578804c6bcd58ed514ffc04fcb433b3bd75d4452575ffda57a0707"},
        [NG_DOTEMU_Z80] = {"mslug3_game_z80", 524288, "76ae674442bcabfa8cad03e8048d38a7755d916a3a9d3a2b9ca835091cec3347"},
        [NG_DOTEMU_ADPCM] = {"mslug3_adpcm", 16777216, "22b5b66ac8005ee9ceefb8129494aba98fdeb7017e34dc184946ecc3775be631"},
    },
    .gog_p1_sha256 = "2d2ee86a3f19b0776727ff01304e69217b3872ecaf26a161b760698410df4dd4",
    .mame = MAME,
    .n_mame = (int)(sizeof MAME / sizeof MAME[0]),
    .crypt = &MSLUG3_CRYPT,
    .cart = NG_CART_SMA,
    .fix_bank = NG_FIX_BANK_ROWS,
    .sma_bank_reg = 0x2FFFE4,
    .sma_bank_bits = {3, 6, 9, 12, 14, 15},
    .sma_banks = SMA_BANKS,
    .sma_id_addr = 0x2FE446,
    .sma_id = 0x9A37,
};

const NgGame *const ng_game = &GAME;
