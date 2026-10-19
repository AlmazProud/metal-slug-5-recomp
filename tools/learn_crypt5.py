"""Turns the black-box maps of Metal Slug 5's encrypted ROMs (tools/probe_decryption.py: MAME as an
oracle fed with synthetic patterns, no game data and no MAME code) into a compact description, and
checks it on the user's MAME set against the regions MAME built from it (Phase 0's dumps).

Program (NEO-PVC, 16-bit words, input = 268-p1cr.p1 + 268-p2cr.p2, 4 M words):
  output word i (22 bits): block k = bits 19-21; input word = PVC_BASE[k] ^ the GF(2)-linear map of
  bits 0-18 given by its columns (PVC_COLS0 for block 0, PVC_COLS for the others); the word's bits
  are permuted by one of three permutations (PVC_PERM[PVC_CLASS[bit 0 | k << 1]]) and XORed with
  PVC_XOR[bits 0-3 | k << 4].
ADPCM-A (PCM2, bytes, input = 268-v1c.v1 + 268-v2c.v2, 16 MB):
  output byte i: input = PCM2_BASE + the sum of PCM2_WEIGHTS of i's set bits (mod 16 MB), XORed
  with PCM2_XOR[i & 7].
Sprites and fix (CMC50): Metal Slug 3's CMC42 form (tools/learn_cmc.py), other tables; the fix
  layer is 128 KB of the decrypted sprites.

Usage:
  python tools/learn_crypt5.py --maps analysis/phase0/probe --set roms/mslug5.zip
        --dumps roms/decrypted [--header src/games/mslug5/crypt_tables.h]
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from learn_cmc import check, learn_sprites, sprites_decrypt  # noqa: E402

MB = 1 << 20


def read_set(path: Path, name: str) -> bytes:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            return z.read(name)
    return (path / name).read_bytes()


def learn_program(maps: Path) -> dict:
    m = np.load(maps / "maincpu_map.npz")
    sigma, pi, xor = m["sigma"].astype(np.int64), m["pi"], m["xor"].astype(np.int64)
    check("program: no constant words", not bool(m["const"].any()))
    n = len(sigma)
    i = np.arange(n, dtype=np.int64)
    k = i >> 19
    t = {"BASE": [int(sigma[b << 19]) for b in range(8)]}
    t["COLS0"] = [int(sigma[1 << b] ^ sigma[0]) for b in range(19)]
    t["COLS"] = [int(sigma[(1 << 19) | (1 << b)] ^ sigma[1 << 19]) for b in range(19)]
    pred = np.array(t["BASE"], np.int64)[k]
    for b in range(19):
        col = np.where(k == 0, t["COLS0"][b], t["COLS"][b])
        pred ^= np.where(i & (1 << b), col, 0)
    check("program: address = block base ^ linear map of bits 0-18", bool((pred == sigma).all()))
    perms, cls = np.unique(pi, axis=0, return_inverse=True)
    cls = cls.reshape(-1)
    t["PERM"] = [[int(x) for x in p] for p in perms]
    key = (i & 1) | (k << 1)
    t["CLASS"] = [int(cls[np.nonzero(key == c)[0][0]]) for c in range(16)]
    check("program: bit permutation by bit 0 and the block", bool((np.array(t["CLASS"])[key] == cls).all()))
    xk = (i & 15) | (k << 4)
    t["XOR"] = [int(xor[np.nonzero(xk == c)[0][0]]) for c in range(128)]
    check("program: XOR by bits 0-3 and the block", bool((np.array(t["XOR"])[xk] == xor).all()))
    return t


def program_decrypt(t: dict, words: np.ndarray) -> np.ndarray:
    n = len(words)
    i = np.arange(n, dtype=np.int64)
    k = i >> 19
    src = np.array(t["BASE"], np.int64)[k]
    for b in range(19):
        src ^= np.where(i & (1 << b), np.where(k == 0, t["COLS0"][b], t["COLS"][b]), 0)
    w = words[src].astype(np.int64)
    cls = np.array(t["CLASS"])[(i & 1) | (k << 1)]
    out = np.zeros(n, np.int64)
    for c, perm in enumerate(t["PERM"]):
        sel = cls == c
        o = np.zeros(int(sel.sum()), np.int64)
        for b in range(16):                      # output bit b = input bit perm[b]
            o |= ((w[sel] >> perm[b]) & 1) << b
        out[sel] = o
    return (out ^ np.array(t["XOR"])[(i & 15) | (k << 4)]).astype(np.uint16)


def learn_pcm2(maps: Path) -> dict:
    m = np.load(maps / "adpcma_map.npz")
    sigma, xor = m["sigma"].astype(np.int64), m["xor"].astype(np.int64)
    check("adpcm: data bits not permuted", bool((m["pi"] == np.arange(8)).all()) and not bool(m["const"].any()))
    n = len(sigma)
    i = np.arange(n, dtype=np.int64)
    t = {"BASE": int(sigma[0]), "WEIGHTS": [int((sigma[1 << b] - sigma[0]) % n) for b in range(24)]}
    pred = np.full(n, t["BASE"], np.int64)
    for b in range(24):
        pred = np.where(i & (1 << b), pred + t["WEIGHTS"][b], pred)
    check("adpcm: address = base + weights of the set bits", bool(((pred % n) == sigma).all()))
    t["XOR"] = [int(xor[c]) for c in range(8)]
    check("adpcm: XOR by bits 0-2", bool((np.array(t["XOR"])[i & 7] == xor).all()))
    return t


def pcm2_decrypt(t: dict, data: np.ndarray) -> np.ndarray:
    n = len(data)
    i = np.arange(n, dtype=np.int64)
    src = np.full(n, t["BASE"], np.int64)
    for b in range(24):
        src = np.where(i & (1 << b), src + t["WEIGHTS"][b], src)
    return (data[src % n] ^ np.array(t["XOR"], np.uint8)[i & 7]).astype(np.uint8)


def learn_fix(maps: Path, t: dict) -> dict:
    """The fix layer: fix byte k = decrypted sprite byte FIX_BASE ^ (linear map of k's bits)."""
    f = np.load(maps / "fixed_map.npz")
    fs, fx = f["sigma"].astype(np.int64), f["xor"].astype(np.int64)
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
    spr = (b0 | b1 << 8 | b2 << 16) * 4 + q
    check("fix: decrypted sprite bytes, no extra XOR", bool((fx == (t["X"][q, b0] ^ t["Y"][q, a1])).all()))
    nb = len(fs).bit_length() - 1
    k = np.arange(len(fs))
    cols = [int(spr[1 << b] ^ spr[0]) for b in range(nb)]
    pred = np.full(len(fs), spr[0])
    for b in range(nb):
        pred ^= np.where((k >> b) & 1, cols[b], 0)
    check("fix: sprite byte = base ^ linear map of the fix byte number", bool((pred == spr).all()))
    return {"FIX_BASE": int(spr[0]), "FIX_COLS": cols}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--maps", type=Path, required=True)
    ap.add_argument("--set", type=Path, required=True)
    ap.add_argument("--dumps", type=Path, required=True)
    ap.add_argument("--header", type=Path)
    a = ap.parse_args()

    print("program (NEO-PVC)")
    pt = learn_program(a.maps)
    words = np.frombuffer(read_set(a.set, "268-p1cr.p1") + read_set(a.set, "268-p2cr.p2"), "<u2")
    out = program_decrypt(pt, words)
    ref = np.frombuffer((a.dumps / "maincpu.bin").read_bytes(), "<u2")
    check("program: all 8 MB identical to MAME's region", bool((out == ref).all()))

    print("adpcm (PCM2)")
    at = learn_pcm2(a.maps)
    data = np.frombuffer(read_set(a.set, "268-v1c.v1") + read_set(a.set, "268-v2c.v2"), np.uint8)
    check("adpcm: all 16 MB identical to MAME's region",
          bool((pcm2_decrypt(at, data) == np.frombuffer((a.dumps / "adpcma.bin").read_bytes(), np.uint8)).all()))

    print("sprites (CMC50)")
    st = learn_sprites(a.maps)
    img = np.empty(64 * MB, np.uint8)
    for k in range(4):
        img[k * 16 * MB:(k + 1) * 16 * MB:2] = np.frombuffer(read_set(a.set, f"268-c{2 * k + 1}c.c{2 * k + 1}"), np.uint8)
        img[k * 16 * MB + 1:(k + 1) * 16 * MB:2] = np.frombuffer(read_set(a.set, f"268-c{2 * k + 2}c.c{2 * k + 2}"), np.uint8)
    spr = sprites_decrypt(st, img)
    check("sprites: all 64 MB identical to MAME's region",
          bool((spr == np.frombuffer((a.dumps / "sprites.bin").read_bytes(), np.uint8)).all()))
    print("fix layer")
    fx = learn_fix(a.maps, st)
    k = np.arange(128 * 1024)
    idx = np.full(len(k), fx["FIX_BASE"])
    for b, c in enumerate(fx["FIX_COLS"]):
        idx ^= np.where((k >> b) & 1, c, 0)
    check("fix: all 128 KB identical to MAME's region",
          bool((spr[idx] == np.frombuffer((a.dumps / "fixed.bin").read_bytes(), np.uint8)).all()))
    if a.header:
        write_header(a.header, pt, at, st, fx)
    return 0


def write_header(path: Path, pt: dict, at: dict, st: dict, fx: dict) -> None:
    def arr(ctype, name, v, fmt="0x{:02X}", per=16):
        v = [int(x) for x in v]
        rows = [", ".join(fmt.format(x) for x in v[i:i + per]) for i in range(0, len(v), per)]
        return f"static const {ctype} {name}[{len(v)}] = {{\n    " + ",\n    ".join(rows) + ",\n};\n"
    out = ["/* Generated by tools/learn_crypt5.py from black-box probes of MAME (synthetic patterns, no",
           " * game data, no MAME code); checked on the user's MAME set against MAME's regions. Metal Slug",
           " * 5's NEO-PVC program, PCM2 ADPCM-A and CMC50 sprite and fix encryption (docs/PHASE5_LOADER.md).",
           " * Key tables in the repository: authorized by the user (2026-10-18). */",
           "#ifndef MSLUG5_CRYPT_TABLES_H", "#define MSLUG5_CRYPT_TABLES_H", "", "#include <stdint.h>", ""]
    out.append(arr("uint32_t", "PVC_BASE", pt["BASE"], "0x{:06X}", 8))
    out.append(arr("uint32_t", "PVC_COLS0", pt["COLS0"], "0x{:06X}", 8))
    out.append(arr("uint32_t", "PVC_COLS", pt["COLS"], "0x{:06X}", 8))
    out.append("static const uint8_t PVC_PERM[3][16] = {\n" + "".join(
        "    {" + ", ".join(str(x) for x in p) + "},\n" for p in pt["PERM"]) + "};\n")
    out.append(arr("uint8_t", "PVC_CLASS", pt["CLASS"], "{}"))
    out.append(arr("uint16_t", "PVC_XOR", pt["XOR"], "0x{:04X}", 8))
    out.append(f"static const uint32_t PCM2_BASE = 0x{at['BASE']:06X};\n")
    out.append(arr("uint32_t", "PCM2_WEIGHTS", at["WEIGHTS"], "0x{:06X}", 8))
    out.append(arr("uint8_t", "PCM2_XOR", at["XOR"]))
    for nm in ("T1", "T2", "T3", "T4", "T5", "M1", "M2", "E1", "E2"):
        out.append(arr("uint8_t", f"CMC_{nm}", st[nm]))
    for q in range(4):
        out.append(arr("uint8_t", f"CMC_X{q}", st["X"][q]))
        out.append(arr("uint8_t", f"CMC_Y{q}", st["Y"][q]))
    out.append(arr("uint8_t", "CMC_BASE_ORDER", st["BASE"]))
    out.append(f"static const uint32_t CMC_FIX_BASE = 0x{fx['FIX_BASE']:X};")
    out.append(f"static const uint32_t CMC_FIX_COLS[{len(fx['FIX_COLS'])}] = {{" + ", ".join(f"0x{c:X}" for c in fx["FIX_COLS"]) + "};")
    out += ["", "#endif", ""]
    path.write_text("\n".join(out), encoding="utf-8")
    print(f"header -> {path}")


if __name__ == "__main__":
    sys.exit(main())
