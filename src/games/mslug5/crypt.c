/* Metal Slug 5: decryption of the MAME set's cartridge files (the game has no PC release). Learned
 * as a black box: tools/probe_decryption.py fed MAME synthetic patterns (no game data, no MAME
 * code) and tools/learn_crypt5.py reduced the maps to the tables of crypt_tables.h, checked on the
 * user's MAME set against the regions MAME built from it: program, sprites, fix, M1 and samples
 * identical (docs/PHASE5_LOADER.md). The output has the runtime's layout (the decrypted reference
 * files of Phases 2-4: MAME's regions in the PC releases' file formats).
 */
#include <stdlib.h>
#include <string.h>

#include "crypt_tables.h"
#include "neogeo.h"

/* ------------------------------------------------------------------ program (NEO-PVC) */
/* Words of 268-p1cr.p1 + 268-p2cr.p2, little-endian in the files. Output word i, block k = bits
   19-21: input word PVC_BASE[k] ^ the linear map of bits 0-18; the word's bits permuted and XORed
   by bit 0 / bits 0-3 and the block. */
static void program(const uint8_t *p, uint32_t p_size, const uint8_t *chip, uint8_t *out)
{
    (void)chip;
    const uint32_t words = p_size / 2;
    for (uint32_t i = 0; i < words; i++) {
        uint32_t k = i >> 19, src = PVC_BASE[k];
        const uint32_t *cols = k ? PVC_COLS : PVC_COLS0;
        for (int b = 0; b < 19; b++) if (i >> b & 1) src ^= cols[b];
        src %= words;
        uint16_t w = (uint16_t)(p[2 * src] | p[2 * src + 1] << 8), o = 0;
        const uint8_t *perm = PVC_PERM[PVC_CLASS[(i & 1) | k << 1]];
        for (int b = 0; b < 16; b++) o |= (uint16_t)(((w >> perm[b]) & 1) << b);
        o ^= PVC_XOR[(i & 15) | k << 4];
        out[2 * i] = (uint8_t)o;
        out[2 * i + 1] = (uint8_t)(o >> 8);
    }
}

/* ------------------------------------------------------------------ sprites and fix (CMC50) */
/* Metal Slug 3's CMC42 form with CMC50's tables (src/games/mslug3/crypt.c). */
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

/* The fix layer (S format, 128 KB): byte k is sprite byte CMC_FIX_BASE ^ (a linear map of k). */
static void fix(const uint8_t *region, uint8_t *s)
{
    const int bits = (int)(sizeof CMC_FIX_COLS / sizeof CMC_FIX_COLS[0]);
    for (uint32_t k = 0; k < (1u << bits); k++) {
        uint32_t at = CMC_FIX_BASE;
        for (int b = 0; b < bits; b++) if (k >> b & 1) at ^= CMC_FIX_COLS[b];
        s[k] = region[at];
    }
}

/* ------------------------------------------------------------------ samples (PCM2) */
/* Output byte i: input byte PCM2_BASE + the weights of i's set bits (mod the size), XORed by i's
   low 3 bits. */
static void adpcm(uint8_t *v, uint32_t size)
{
    uint8_t *in = malloc(size);
    if (!in) return;
    memcpy(in, v, size);
    for (uint32_t i = 0; i < size; i++) {
        uint64_t src = PCM2_BASE;
        for (int b = 0; b < 24; b++) if (i >> b & 1) src += PCM2_WEIGHTS[b];
        v[i] = in[src % size] ^ PCM2_XOR[i & 7];
    }
    free(in);
}

/* ------------------------------------------------------------------ the M1 (CMC50, keyed) */
static uint32_t gather(uint32_t v, const uint8_t *bits)
{
    uint32_t o = 0;
    for (int k = 0; k < 8; k++) o |= ((v >> bits[k]) & 1) << k;
    return o;
}

/* A byte permutation keyed by the 16-bit sum of the file's first 64 KB, known for the real set's
   key only. Each 64 KB bank stays in place; within bank k, file address bits A and B give
   X = M1_PA[k][A] ^ M1_T1[k][B], Y = M1_PB[k][B] ^ M1_T2[k][X], placed at M1_XPOS / M1_YPOS. */
static int z80(uint8_t *m, uint32_t size)
{
    uint32_t sum = 0;
    for (uint32_t i = 0; i < 0x10000 && i < size; i++) sum += m[i];
    if ((sum & 0xFFFF) != M1_KEY || size != 0x80000) return -1;
    uint8_t *in = malloc(size);
    if (!in) return -1;
    memcpy(in, m, size);
    for (uint32_t k = 0; k < 8; k++)
        for (uint32_t x = 0; x < 0x10000; x++) {
            uint32_t a = gather(x, M1_A_BITS), b = gather(x, M1_B_BITS);
            uint32_t X = M1_PA[k][a] ^ M1_T1[k][b];
            uint32_t Y = M1_PB[k][b] ^ M1_T2[k][X];
            uint32_t r = 0;
            for (int i = 0; i < 8; i++) r |= ((X >> i) & 1) << M1_XPOS[k][i] | ((Y >> i) & 1) << M1_YPOS[k][i];
            m[k << 16 | r] = in[k << 16 | x];
        }
    free(in);
    return 0;
}

const NgMameCrypt MSLUG5_CRYPT = {
    .program_size = 8 * 1024 * 1024,
    .program = program,
    .sprites = sprites,
    .fix_size = 128 * 1024,
    .fix = fix,
    .z80 = z80,
    .adpcm = adpcm,
};
