"""Turns the black-box maps of Metal Slug 3's encrypted ROMs (tools/probe_decryption.py: MAME as an
oracle fed with synthetic patterns, no game data and no MAME code) into a compact description, and
checks it on the user's MAME set against the decrypted reference (the GOG files).

Program (NEO-SMA, 16-bit words, input = 256-pg1.p1 + 256-pg2.p2 read little-endian):
  every word's 16 bits are permuted (PROGRAM_DATA: input bit b -> output bit);
  output words 0x80000-0x47FFFF (P2): input = (j & ~0x7FFF) | bits(j & 0x7FFF) weighted by P2_WEIGHTS,
    j = output - 0x80000;
  output words 0-0x5FFFF (P1): input = 0x268000 + sum of P1_WEIGHTS of the set bits (an addition);
  output words 0x60000-0x7FFFF: green.neo-sma as it is.

Sprites (CMC42, input = the C ROMs interleaved in pairs: c1/c2 even/odd bytes, then c3/c4...):
  units of 4 bytes; unit address v = a0 | a1 << 8 | a2 << 16 (bytes);
  output unit: b0 = a0 ^ T1[a1]; b2 = a2 ^ T2[a1] ^ T3[b0]; b1 = a1 ^ T4[b0] ^ T5[b2];
  byte order: positions 1 and 2 swap if M1[a1] ^ M2[a2], 0 and 3 if E1[a1] ^ E2[a2] (on top of the
    base order); then output byte q ^= X[q][b0] ^ Y[q][a1].
Fix layer: derived from the decrypted sprites (FIX_* below).

Usage:
  python tools/learn_cmc.py --maps analysis/phase0/probe --set roms/mame/mslug3 --ref roms
        [--header src/games/mslug3/cmc_tables.h]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_roms import fix_dotemu_to_neogeo, sprites_dotemu_to_region  # noqa: E402

MB = 1 << 20


def check(name: str, ok: bool) -> None:
    print(f"  {name}: {'OK' if ok else 'FAILED'}")
    if not ok:
        sys.exit(1)


def learn_sprites(maps: Path) -> dict[str, np.ndarray]:
    m = np.load(maps / "sprites_map.npz")
    s, x = m["sigma"].astype(np.int64), m["xor"].astype(np.int64)
    check("data bits not permuted", bool((np.unique(m["pi"], axis=0) == np.arange(8)).all()))
    n = len(s) // 4
    o = np.arange(len(s))
    v, p = s >> 2, s & 3
    Q = np.empty((n, 4), np.int64)
    C = np.empty((n, 4), np.int64)
    Q[v, p] = o & 3
    C[v, p] = x
    G = np.empty(n, np.int64)
    G[v[0::4]] = np.arange(n)                          # input unit -> output unit
    V = np.arange(n)
    a0, a1, a2 = V & 0xFF, (V >> 8) & 0xFF, V >> 16
    b0, b1, b2 = G & 0xFF, (G >> 8) & 0xFF, G >> 16

    def at(**fixed):
        sel = np.ones(n, bool)
        for k, val in fixed.items():
            sel &= {"a0": a0, "a1": a1, "a2": a2, "b0": b0, "b2": b2}[k] == val
        return sel

    t = {}
    sel = at(a0=0, a2=0); t["T1"] = np.zeros(256, np.int64); t["T1"][a1[sel]] = b0[sel]
    d2 = b2 ^ a2
    sel = (b0 == 0) & (a2 == 0); t["T2"] = np.zeros(256, np.int64); t["T2"][a1[sel]] = d2[sel]
    sel = (a1 == 0) & (a2 == 0); t["T3"] = np.zeros(256, np.int64); t["T3"][b0[sel]] = d2[sel] ^ t["T2"][0]
    d1 = b1 ^ a1
    sel = b0 == 0; t["T5"] = np.zeros(256, np.int64); t["T5"][b2[sel]] = d1[sel]
    sel = b2 == 0; t["T4"] = np.zeros(256, np.int64); t["T4"][b0[sel]] = d1[sel] ^ t["T5"][0]
    pred = np.empty(n, np.int64)
    p0 = a0 ^ t["T1"][a1]
    p2 = a2 ^ t["T2"][a1] ^ t["T3"][p0]
    p1 = a1 ^ t["T4"][p0] ^ t["T5"][p2]
    pred = p0 | p1 << 8 | p2 << 16
    check("unit address: three XOR steps with T1-T5", bool((pred == G).all()))

    base = Q[0].copy()                                  # unit 0: no swap by definition below
    mid = (Q[:, 1] != base[1]).astype(np.int64)
    end = (Q[:, 0] != base[0]).astype(np.int64)
    for nm, sw in (("M", mid), ("E", end)):
        s2 = np.zeros(256, np.int64); s1 = np.zeros(256, np.int64)
        sel = a1 == 0; s2[a2[sel]] = sw[sel]
        sel = a2 == 0; s1[a1[sel]] = sw[sel] ^ s2[0]
        t[nm + "1"], t[nm + "2"] = s1, s2
    sm = t["M1"][a1] ^ t["M2"][a2]
    se = t["E1"][a1] ^ t["E2"][a2]
    swap = lambda q, cond, i, j: np.where(cond, np.where(q == i, j, np.where(q == j, i, q)), q)
    predq = np.empty_like(Q)
    for pp in range(4):
        q = np.full(n, base[pp])
        q = swap(q, sm == 1, base[1], base[2])
        q = swap(q, se == 1, base[0], base[3])
        predq[:, pp] = q
    check("byte order: base order and two swaps (M1/M2, E1/E2)", bool((predq == Q).all()))

    Cq = np.empty_like(C)
    for pp in range(4):
        Cq[V, Q[:, pp]] = C[:, pp]
    t["X"] = np.zeros((4, 256), np.int64); t["Y"] = np.zeros((4, 256), np.int64)
    for q in range(4):
        sel = b0 == 0; t["Y"][q][a1[sel]] = Cq[sel, q]
        sel = a1 == 0; t["X"][q][b0[sel]] = Cq[sel, q] ^ t["Y"][q][0]
    predc = t["X"][:, b0].T ^ t["Y"][:, a1].T
    check("data XOR: X[q][b0] ^ Y[q][a1]", bool((predc == Cq).all()))
    t["BASE"] = base
    return t


def sprites_decrypt(t: dict, img: np.ndarray) -> np.ndarray:
    n = len(img) // 4
    V = np.arange(n)
    a0, a1, a2 = V & 0xFF, (V >> 8) & 0xFF, V >> 16
    b0 = a0 ^ t["T1"][a1]
    b2 = a2 ^ t["T2"][a1] ^ t["T3"][b0]
    b1 = a1 ^ t["T4"][b0] ^ t["T5"][b2]
    out_unit = b0 | b1 << 8 | b2 << 16
    base = t["BASE"]
    sm = (t["M1"][a1] ^ t["M2"][a2]) == 1
    se = (t["E1"][a1] ^ t["E2"][a2]) == 1
    src = img.reshape(n, 4)
    out = np.empty((n, 4), np.uint8)
    for p in range(4):
        q = np.full(n, base[p])
        q = np.where(sm & (q == base[1]), -1, q); q = np.where(sm & (q == base[2]), base[1], q); q = np.where(q == -1, base[2], q)
        q = np.where(se & (q == base[0]), -2, q); q = np.where(se & (q == base[3]), base[0], q); q = np.where(q == -2, base[3], q)
        out[out_unit, q] = src[:, p] ^ (t["X"][q, b0] ^ t["Y"][q, a1]).astype(np.uint8)
    return out.reshape(-1)


def learn_fix(maps: Path, t: dict) -> dict:
    """The fix layer from the decrypted sprites: fix byte k = sprites byte F(k) (no XOR)."""
    f = np.load(maps / "fixed_map.npz")
    fs, fx = f["sigma"].astype(np.int64), f["xor"].astype(np.int64)
    # input byte i lands at output (unit G(i>>2), position q) with XOR; follow the fixed map's
    # input byte through the sprite decryption to a decrypted sprite byte.
    n = 16 * MB
    V = fs >> 2
    a0, a1, a2 = V & 0xFF, (V >> 8) & 0xFF, V >> 16
    b0 = a0 ^ t["T1"][a1]
    b2 = a2 ^ t["T2"][a1] ^ t["T3"][b0]
    b1 = a1 ^ t["T4"][b0] ^ t["T5"][b2]
    base = t["BASE"]
    p = fs & 3
    sm = (t["M1"][a1] ^ t["M2"][a2]) == 1
    se = (t["E1"][a1] ^ t["E2"][a2]) == 1
    q = base[p]
    q = np.where(sm & (q == base[1]), -1, q); q = np.where(sm & (q == base[2]), base[1], q); q = np.where(q == -1, base[2], q)
    q = np.where(se & (q == base[0]), -2, q); q = np.where(se & (q == base[3]), base[0], q); q = np.where(q == -2, base[3], q)
    spr_byte = (b0 | b1 << 8 | b2 << 16) * 4 + q
    xr = t["X"][q, b0] ^ t["Y"][q, a1]
    check("fix: decrypted sprite bytes, no extra XOR", bool((fx == xr).all()))
    k = np.arange(len(fs))
    lo = spr_byte - spr_byte.min()
    cols = [int(lo[1 << b] ^ lo[0]) for b in range(19)]
    pred = np.zeros_like(lo)
    for b in range(19):
        pred ^= np.where((k >> b) & 1, cols[b], 0)
    check("fix: a bit permutation of the last sprite bytes", bool((pred ^ lo[0] == lo).all()))
    return {"FIX_BASE": int(spr_byte.min() + lo[0]), "FIX_COLS": cols}


def program_check(setdir: Path, ref: Path) -> None:
    inp = np.frombuffer((setdir / "256-pg1.p1").read_bytes() + (setdir / "256-pg2.p2").read_bytes(), "<u2").astype(np.int64)
    gog = np.frombuffer((ref / "mslug3_game_m68k").read_bytes(), "<u2").astype(np.int64)
    pi = [9, 11, 7, 12, 15, 1, 0, 8, 6, 2, 3, 14, 5, 10, 13, 4]
    p1w = [0x1000, 0x8000, 0x10000, 0x2000, 0x100, 0x40, 0x400, 0x20, 0x1, 0x800, 0x2, 0x80, 0x10, 0x4000, 0x4, 0x20000, 0x200, 0x8, 0x40000]
    p2w = [0x1000, 0x1, 0x4000, 0x20, 0x200, 0x4, 0x400, 0x8, 0x80, 0x40, 0x10, 0x2000, 0x2, 0x100, 0x800]

    def data(w):
        o = np.zeros_like(w)
        for b in range(16):
            o |= ((w >> b) & 1) << pi[b]
        return o
    out = np.zeros(0x480000, np.int64)
    i = np.arange(0x60000)
    out[:0x60000] = data(inp[0x268000 + sum(((i >> k) & 1) * w for k, w in enumerate(p1w))])
    j = np.arange(0x400000)
    out[0x80000:] = data(inp[(j & ~0x7FFF) | sum(((j >> k) & 1) * w for k, w in enumerate(p2w))])
    out[0x60000:0x80000] = np.frombuffer((setdir / "green.neo-sma").read_bytes(), "<u2")
    check("program: all 9 MB identical to the reference", bool((out == gog).all()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", type=Path, required=True)
    ap.add_argument("--set", type=Path, required=True)
    ap.add_argument("--ref", type=Path, required=True)
    ap.add_argument("--header", type=Path)
    a = ap.parse_args()
    print("program")
    program_check(a.set, a.ref)
    print("sprites (from the black-box map)")
    t = learn_sprites(a.maps)
    img = np.empty(64 * MB, np.uint8)
    for k in range(4):
        odd = np.frombuffer((a.set / f"256-c{2 * k + 1}.c{2 * k + 1}").read_bytes(), np.uint8)
        even = np.frombuffer((a.set / f"256-c{2 * k + 2}.c{2 * k + 2}").read_bytes(), np.uint8)
        img[k * 16 * MB:(k + 1) * 16 * MB:2] = odd
        img[k * 16 * MB + 1:(k + 1) * 16 * MB:2] = even
    spr = sprites_decrypt(t, img)
    tiles = (a.ref / "mslug3_tiles").read_bytes()          # DotEmu layout -> the board's
    ref = np.concatenate([sprites_dotemu_to_region(tiles[k * 16 * MB:(k + 1) * 16 * MB]) for k in range(4)])
    check("sprites: all 64 MB identical to the reference", bool((spr == ref).all()))
    print("fix layer")
    fx = learn_fix(a.maps, t)
    k = np.arange(512 * 1024)
    idx = fx["FIX_BASE"] ^ sum(((k >> b) & 1) * c for b, c in enumerate(fx["FIX_COLS"]))
    fix_ref = np.frombuffer(fix_dotemu_to_neogeo((a.ref / "mslug3_game_sfix").read_bytes()), np.uint8)
    check("fix: all 512 KB identical to the reference", bool((spr[idx] == fix_ref).all()))
    if a.header:
        write_header(a.header, t, fx)
    return 0


def write_header(path: Path, t: dict, fx: dict) -> None:
    def arr(name, v, per=16):
        v = [int(x) for x in v]
        rows = [", ".join(f"0x{x:02X}" for x in v[i:i + per]) for i in range(0, len(v), per)]
        return f"static const uint8_t {name}[{len(v)}] = {{\n    " + ",\n    ".join(rows) + ",\n};\n"
    out = ["/* Generated by tools/learn_cmc.py from black-box probes of MAME (synthetic patterns, no game",
           " * data, no MAME code); checked on the MAME set against the decrypted reference. Metal Slug 3's",
           " * CMC42 sprite encryption: see src/neogeo/cmc.c. */",
           "#ifndef MSLUG3_CMC_TABLES_H", "#define MSLUG3_CMC_TABLES_H", "", "#include <stdint.h>", ""]
    for nm in ("T1", "T2", "T3", "T4", "T5"):
        out.append(arr(f"CMC_{nm}", t[nm]))
    for nm in ("M1", "M2", "E1", "E2"):
        out.append(arr(f"CMC_{nm}", t[nm]))
    for q in range(4):
        out.append(arr(f"CMC_X{q}", t["X"][q]))
        out.append(arr(f"CMC_Y{q}", t["Y"][q]))
    out.append(arr("CMC_BASE_ORDER", t["BASE"]))
    out.append(f"static const uint32_t CMC_FIX_BASE = 0x{fx['FIX_BASE']:X};")
    out.append("static const uint32_t CMC_FIX_COLS[19] = {" + ", ".join(f"0x{c:X}" for c in fx["FIX_COLS"]) + "};")
    out += ["", "#endif", ""]
    path.write_text("\n".join(out), encoding="utf-8")
    print(f"header -> {path}")


if __name__ == "__main__":
    sys.exit(main())
