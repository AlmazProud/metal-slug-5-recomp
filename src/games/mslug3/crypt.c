/* Metal Slug 3: decryption of the MAME set's cartridge files (the PC release's files are already
 * decrypted). Learned as a black box: tools/probe_decryption.py fed MAME synthetic patterns (no
 * game data, no MAME code) and tools/learn_cmc.py reduced the maps to the description below,
 * checked on a MAME set against the GOG files: program, sprites and fix identical (docs/
 * PHASE5_LOADER.md).
 */
#include <stdlib.h>
#include <string.h>

#include "cmc_tables.h"
#include "neogeo.h"

/* ------------------------------------------------------------------ program (NEO-SMA) */
/* Words of 256-pg1.p1 + 256-pg2.p2, little-endian in the files. Input bit b -> output bit. */
static const uint8_t PROGRAM_DATA[16] = {9, 11, 7, 12, 15, 1, 0, 8, 6, 2, 3, 14, 5, 10, 13, 4};
/* Output words 0-0x5FFFF (the fixed 768 KB): input word = 0x268000 + the weights of the set bits
   of the output word number (an addition). */
static const uint32_t P1_WEIGHTS[19] = {
    0x1000, 0x8000, 0x10000, 0x2000, 0x100, 0x40, 0x400, 0x20, 0x1, 0x800,
    0x2, 0x80, 0x10, 0x4000, 0x4, 0x20000, 0x200, 0x8, 0x40000,
};
/* Output words 0x80000-0x47FFFF (P2): the low 15 bits of j = output - 0x80000 are permuted. */
static const uint32_t P2_WEIGHTS[15] = {
    0x1000, 0x1, 0x4000, 0x20, 0x200, 0x4, 0x400, 0x8, 0x80, 0x40, 0x10, 0x2000, 0x2, 0x100, 0x800,
};

static uint16_t data_bits(uint16_t w)
{
    uint16_t o = 0;
    for (int b = 0; b < 16; b++) o |= (uint16_t)(((w >> b) & 1) << PROGRAM_DATA[b]);
    return o;
}

static void put(uint8_t *out, uint32_t word, uint16_t v)
{
    out[2 * word] = (uint8_t)v;
    out[2 * word + 1] = (uint8_t)(v >> 8);
}

/* p: 8 MB (pg1 + pg2), chip: green.neo-sma (256 KB). out: 9 MB, the PC release's program. */
static void program(const uint8_t *p, uint32_t p_size, const uint8_t *chip, uint8_t *out)
{
    const uint32_t words = p_size / 2;
#define IN(i) ((uint16_t)(p[2 * ((i) % words)] | p[2 * ((i) % words) + 1] << 8))
    for (uint32_t i = 0; i < 0x60000; i++) {
        uint32_t src = 0x268000;
        for (int k = 0; k < 19; k++) if (i >> k & 1) src += P1_WEIGHTS[k];
        put(out, i, data_bits(IN(src)));
    }
    memcpy(out + 0xC0000, chip, 0x40000);
    for (uint32_t j = 0; j < 0x400000; j++) {
        uint32_t src = j & ~0x7FFFu;
        for (int k = 0; k < 15; k++) if (j >> k & 1) src |= P2_WEIGHTS[k];
        put(out, 0x80000 + j, data_bits(IN(src)));
    }
#undef IN
}

/* ------------------------------------------------------------------ sprites (CMC42) */
/* image: the C ROMs interleaved in pairs (c1/c2 even/odd bytes, then c3/c4...), 4-byte units at
   unit address a0 | a1 << 8 | a2 << 16. region: the board's decrypted sprite data. */
static void sprites(const uint8_t *image, uint32_t size, uint8_t *region)
{
    static const uint8_t *const X[4] = {CMC_X0, CMC_X1, CMC_X2, CMC_X3};
    static const uint8_t *const Y[4] = {CMC_Y0, CMC_Y1, CMC_Y2, CMC_Y3};
    const uint8_t *base = CMC_BASE_ORDER;
    for (uint32_t v = 0; v < size / 4; v++) {
        uint8_t a0 = (uint8_t)v, a1 = (uint8_t)(v >> 8), a2 = (uint8_t)(v >> 16);
        uint8_t b0 = a0 ^ CMC_T1[a1];
        uint8_t b2 = a2 ^ CMC_T2[a1] ^ CMC_T3[b0];
        uint8_t b1 = a1 ^ CMC_T4[b0] ^ CMC_T5[b2];
        uint32_t out = ((uint32_t)b0 | (uint32_t)b1 << 8 | (uint32_t)b2 << 16) * 4;
        int mid = CMC_M1[a1] ^ CMC_M2[a2], end = CMC_E1[a1] ^ CMC_E2[a2];
        for (int p = 0; p < 4; p++) {
            int q = base[p];
            if (mid && q == base[1]) q = base[2];
            else if (mid && q == base[2]) q = base[1];
            if (end && q == base[0]) q = base[3];
            else if (end && q == base[3]) q = base[0];
            region[out + (uint32_t)q] = image[v * 4 + (uint32_t)p] ^ X[q][b0] ^ Y[q][a1];
        }
    }
}

/* The fix layer (S format, 512 KB) from the decrypted sprites: byte k is sprite byte
   CMC_FIX_BASE ^ (a bit permutation of k). */
static void fix(const uint8_t *region, uint8_t *s)
{
    for (uint32_t k = 0; k < 512 * 1024; k++) {
        uint32_t at = CMC_FIX_BASE;
        for (int b = 0; b < 19; b++) if (k >> b & 1) at ^= CMC_FIX_COLS[b];
        s[k] = region[at];
    }
}

const NgMameCrypt MSLUG3_CRYPT = {
    .program_size = 9 * 1024 * 1024,
    .program = program,
    .sprites = sprites,
    .fix_size = 512 * 1024,
    .fix = fix,
};
