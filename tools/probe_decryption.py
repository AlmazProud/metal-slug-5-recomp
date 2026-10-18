"""Learns how MAME turns a cartridge's ROM files into its memory regions, by black-box probing.

MAME is used as an oracle, not as a source: synthetic ROM files with known patterns (never game
data) are loaded into MAME's `mslug5` driver, the regions it builds are dumped right after start
(tools/mame/dump_region.lua) and the transformation is deduced from the patterns. No MAME code is
read or copied. Adapted from the Metal Slug 3 port's tool (MIT, Copyright (c) 2026 AlmazProud).

Usage:
    python tools/probe_decryption.py learn TARGET --work DIR [--base DIR] [--mame EXE]
    python tools/probe_decryption.py check TARGET --work DIR [--base DIR] [--dumps DIR]

Targets (the files of the `mslug5` set; one input image each, cut into the files):
  program   268-p1cr.p1 + 268-p2cr.p2 (8 MB, 16-bit words, file byte order) -> :cslot1:maincpu
  graphics  268-c1c..c8c (64 MB, bytes in region order: even bytes from the odd C ROMs, odd
            bytes from the even ones) -> :cslot1:sprites (64 MB) and :cslot1:fixed (128 KB)
  audio     268-m1.m1 (512 KB, bytes) -> :cslot1:audiocpu (576 KB)
  adpcm     268-v1c.v1 + 268-v2c.v2 (16 MB, bytes) -> :cslot1:ymsnd:adpcma

learn: probes all zero, all ones, three random images (GF(2) linearity: f(a)^f(b)^f(a^b)^f(0)
  must be 0), one probe per address bit (unit j all ones when bit k of j is set) and one per data
  bit (every unit = 1 << b). Model (checked on every probe; the tool stops and says where it
  breaks): every output unit is a constant, or pi_i(input unit sigma(i)) XOR c(i), with sigma an
  address map and pi_i a permutation of the unit's bits. Saved to <work>/<region>_map.npz.
  The model is then checked once more by predicting MAME's output for a fresh random image.
  The M1 (audio) is not affine: its byte permutation depends on the 16-bit sum of the file's
  first 64 KB (the key), so it is learned for the real set's key only (learn_keyed).
check: applies the learned maps to the real set (from --base) and compares the result with the
  regions MAME dumped from it (--dumps, default <workspace>/roms/decrypted: maincpu.bin,
  sprites.bin, fixed.bin, audiocpu.bin, adpcma.bin).

--base holds the complete set (mslug5.zip and neogeo/, default <workspace>/roms) for the files
that are not probed; the probe files go in a folder that comes first in -rompath.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np

MB = 1 << 20
KB = 1 << 10
GAME = "mslug5"
ROOT = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[1]
LUA = REPO / "tools" / "mame" / "dump_region.lua"


def run_mame(mame: Path, rompath: list[Path], work: Path, regions: dict[str, Path]) -> None:
    nv = work / "nvram"
    shutil.rmtree(nv, ignore_errors=True)
    nv.mkdir(parents=True)
    for p in regions.values():
        p.unlink(missing_ok=True)
    env = dict(os.environ, PD_REGIONS=";".join(f"{t}={p}" for t, p in regions.items()))
    r = subprocess.run([str(mame), GAME, "-bios", "us", "-rompath", ";".join(map(str, rompath)),
                        "-nvram_directory", str(nv), "-cfg_directory", str(nv), "-skip_gameinfo",
                        "-video", "none", "-sound", "none", "-seconds_to_run", "1",
                        "-autoboot_script", str(LUA)],
                       cwd=mame.parent, env=env, capture_output=True, text=True)
    for p in regions.values():
        if not p.is_file():
            sys.exit(f"MAME did not dump {p}:\n{r.stdout}\n{r.stderr}")


class Target:
    """What is probed: the files an input image is cut into, and which regions to dump."""

    def __init__(self, name: str, dtype: str, files: list[tuple[str, int]], regions: dict[str, str],
                 interleave: bool = False):
        self.name, self.dtype, self.files, self.regions = name, dtype, files, regions
        self.interleave = interleave          # C ROMs: pairs of files hold the even / odd bytes
        self.size = sum(s for _, s in files)
        self.units = self.size // np.dtype(dtype).itemsize
        self.bits = np.dtype(dtype).itemsize * 8

    def split(self, image: np.ndarray) -> dict[str, bytes]:
        b = image.astype(self.dtype).tobytes()
        if not self.interleave:
            out, o = {}, 0
            for n, s in self.files:
                out[n], o = b[o:o + s], o + s
            return out
        a = np.frombuffer(b, np.uint8)
        out, o = {}, 0
        for (n0, s0), (n1, s1) in zip(self.files[0::2], self.files[1::2]):
            out[n0] = a[o:o + 2 * s0:2].tobytes()
            out[n1] = a[o + 1:o + 2 * s0:2].tobytes()
            o += s0 + s1
        return out

    def join(self, files: dict[str, bytes]) -> np.ndarray:
        if not self.interleave:
            return np.frombuffer(b"".join(files[n] for n, _ in self.files), self.dtype)
        parts = []
        for (n0, s0), (n1, _) in zip(self.files[0::2], self.files[1::2]):
            p = np.empty(2 * s0, np.uint8)
            p[0::2] = np.frombuffer(files[n0], np.uint8)
            p[1::2] = np.frombuffer(files[n1], np.uint8)
            parts.append(p)
        return np.concatenate(parts).view(self.dtype)


TARGETS = {
    "program": Target("program", "<u2", [("268-p1cr.p1", 4 * MB), ("268-p2cr.p2", 4 * MB)],
                      {":cslot1:maincpu": "maincpu"}),
    "graphics": Target("graphics", "u1", [(f"268-c{i}c.c{i}", 8 * MB) for i in range(1, 9)],
                       {":cslot1:sprites": "sprites", ":cslot1:fixed": "fixed"}, interleave=True),
    "audio": Target("audio", "u1", [("268-m1.m1", 512 * KB)], {":cslot1:audiocpu": "audiocpu"}),
    "adpcm": Target("adpcm", "u1", [("268-v1c.v1", 8 * MB), ("268-v2c.v2", 8 * MB)],
                    {":cslot1:ymsnd:adpcma": "adpcma"}),
}


def run_probe(t: Target, name: str, image: np.ndarray, mame: Path, base: Path, work: Path) -> dict[str, np.ndarray]:
    pdir = work / f"probe_{name}"
    (pdir / GAME).mkdir(parents=True, exist_ok=True)
    for n, data in t.split(image).items():
        (pdir / GAME / n).write_bytes(data)
    dumps = {tag: work / f"{label}_{name}.bin" for tag, label in t.regions.items()}
    run_mame(mame, [pdir, base], work, dumps)
    shutil.rmtree(pdir)
    out = {}
    for tag, label in t.regions.items():
        out[label] = np.frombuffer(dumps[tag].read_bytes(), t.dtype)
        dumps[tag].unlink()
    print(f"probe {name}: done", flush=True)
    return out


def apply(m: dict[str, np.ndarray], image: np.ndarray, bits: int) -> np.ndarray:
    """Output of a learned map for an input image (units of `bits` bits)."""
    s, p, x, c = m["sigma"], m["pi"], m["xor"], m["const"]
    out = x.astype(np.uint32).copy()
    src = image[np.where(c, 0, s)].astype(np.uint32)
    live = ~c
    for b in range(bits):
        dest = p[:, b].astype(np.int64)
        on = live & (((src >> b) & 1) == 1)
        out[on] ^= (np.uint32(1) << dest[on].astype(np.uint32))
    return out.astype(x.dtype)


def learn(t: Target, mame: Path, base: Path, work: Path) -> None:
    full = (1 << t.bits) - 1
    j = np.arange(t.units, dtype=np.uint32)
    probe = lambda name, image: run_probe(t, name, image.astype(t.dtype), mame, base, work)
    zero = probe("zero", np.zeros(t.units, np.uint32))
    ones = probe("ones", np.full(t.units, full, np.uint32))

    rng = np.random.default_rng(2026)
    a = rng.integers(0, full + 1, t.units, dtype=np.uint32)
    b = rng.integers(0, full + 1, t.units, dtype=np.uint32)
    fa, fb, fab = probe("rand_a", a), probe("rand_b", b), probe("rand_ab", a ^ b)
    for label in zero:
        bad = np.count_nonzero(fa[label] ^ fb[label] ^ fab[label] ^ zero[label])
        print(f"{label}: GF(2) linearity, {bad} units break it", flush=True)
        if bad:
            where = np.flatnonzero(fa[label] ^ fb[label] ^ fab[label] ^ zero[label])
            sys.exit(f"{label}: model broken, not affine (first units {where[:8].tolist()})")

    const, sigma, pi = {}, {}, {}
    for label in zero:
        o0, o1 = zero[label], ones[label]
        const[label] = o0 == o1
        if not np.all((o0 ^ o1)[~const[label]] == full):
            bad = np.flatnonzero(((o0 ^ o1) != full) & ~const[label])
            sys.exit(f"{label}: model broken, {bad.size} units depend on the input but not as a bit "
                     f"permutation of one unit (first {bad[:8].tolist()})")
        sigma[label] = np.zeros(o0.size, np.int32)
        pi[label] = np.full((o0.size, t.bits), -1, np.int8)   # pi[i, b] = output bit of input bit b

    nbits = (t.units - 1).bit_length()
    for k in range(nbits):
        out = probe(f"bit{k:02d}", np.where((j >> k) & 1, full, 0))
        for label in zero:
            d = out[label] ^ zero[label]
            if not np.all((d == 0) | (d == full)):
                bad = np.flatnonzero((d != 0) & (d != full))
                sys.exit(f"{label}: model broken at address bit {k} ({bad.size} units, first {bad[:8].tolist()})")
            sigma[label] |= (d == full).astype(np.int32) << k
    for bit in range(t.bits):
        out = probe(f"data{bit:02d}", np.full(t.units, 1 << bit, np.uint32))
        for label in zero:
            c = const[label]
            d = (out[label] ^ zero[label])[~c].astype(np.uint32)
            if not np.all((d != 0) & ((d & (d - 1)) == 0)):
                sys.exit(f"{label}: model broken, data bit {bit} does not give single bits")
            pi[label][~c, bit] = np.log2(d).astype(np.int8)

    maps = {}
    for label in zero:
        o0, c, s, p = zero[label], const[label], sigma[label], pi[label]
        s[c] = -1
        rows = p[~c]
        if not np.all(np.sort(rows, axis=1) == np.arange(t.bits)):
            sys.exit(f"{label}: model broken, the data map is not a permutation")
        distinct = np.unique(rows, axis=0)
        maps[label] = dict(sigma=s, pi=p, xor=o0, const=c)
        np.savez_compressed(work / f"{label}_map.npz", **maps[label])

        used = np.unique(s[~c])
        xor_units = int(np.count_nonzero(o0[~c]))
        print(f"{label}: {o0.size} output units, {int(c.sum())} constant, "
              f"{int((~c).sum())} from the input; {used.size} distinct input units of {t.units}")
        print(f"{label}: {len(distinct)} distinct data permutations; XOR on {xor_units} units")
        for row in distinct[:4]:
            print("   " + " ".join(f"{b}->{row[b]}" for b in range(t.bits)))

    # A last, independent check: predict MAME's output for a fresh random image.
    r = np.random.default_rng(7).integers(0, full + 1, t.units, dtype=np.uint32).astype(t.dtype)
    got = probe("predict", r)
    for label in zero:
        bad = np.count_nonzero(apply(maps[label], r, t.bits) != got[label])
        print(f"{label}: prediction for a fresh random image, {bad} units differ")
        if bad:
            sys.exit(f"{label}: model broken on the prediction check")


def m1_key(image: np.ndarray) -> int:
    """The M1 permutation's key, as observed: the 16-bit sum of the first 64 KB of the file (two
    inputs with the same sum mod 0x10000 give the same permutation; any other change of that sum
    changes all of it)."""
    return int(image[:0x10000].astype(np.int64).sum()) & 0xFFFF


def learn_keyed(t: Target, mame: Path, base: Path, work: Path) -> None:
    """The M1: a byte permutation that depends on the data (m1_key), so the affine probes cannot be
    used. It is learned for the real set's key only: every probe is a synthetic image whose key is
    made equal to it by a block of compensation bytes. Three probes give the input address of
    every output byte as three base-256 digits; it is done twice with disjoint compensation blocks,
    and an output whose source is a compensation byte of one round is taken from the other."""
    key = m1_key(t.join(read_set(t, base)))
    print(f"real set's key: {key:#06x}")
    n = t.units
    j = np.arange(n, dtype=np.int64)
    rounds = [np.arange(0x0000, 0x0400), np.arange(0x8000, 0x8400)]   # compensation blocks
    decoded, probes = [], []
    for r, comp in enumerate(rounds):
        sigma = np.zeros(0, np.int64)
        for d in range(3):
            img = ((j >> (8 * d)) & 0xFF).astype(np.uint8)
            img[comp] = 0
            need = (key - m1_key(img)) & 0xFFFF       # spread over the block, 255 at most per byte
            vals = np.zeros(comp.size, np.int64)
            vals[:need // 255] = 255
            vals[need // 255] = need % 255
            img[comp] = vals.astype(np.uint8)
            assert m1_key(img) == key
            out = run_probe(t, f"m1_r{r}_d{d}", img, mame, base, work)["audiocpu"].astype(np.int64)
            probes.append((img, out))
            sigma = out if d == 0 else sigma | (out << (8 * d))
        decoded.append(sigma)

    def consistent(c: np.ndarray) -> np.ndarray:
        """Source candidates that reproduce every probe's output."""
        ok = (c >= 0) & (c < n)
        cc = np.where(ok, c, 0)
        for img, out in probes:
            ok &= img[cc] == out
        return ok

    s0, s1 = decoded
    ok0, ok1 = consistent(s0), consistent(s1)
    sigma = np.where(ok0, s0, np.where(ok1, s1, -1))
    ambiguous = ok0 & ok1 & (s0 != s1)
    if (sigma < 0).any() or ambiguous.any():
        sys.exit(f"audiocpu: {int((sigma < 0).sum())} outputs unresolved, {int(ambiguous.sum())} "
                 "ambiguous; model broken")
    body = sigma[0x10000:]
    if np.unique(body).size != n:
        sys.exit("audiocpu: the 512 KB after 0x10000 are not a permutation of the input")
    m = dict(sigma=sigma.astype(np.int32), pi=np.tile(np.arange(8, dtype=np.int8), (sigma.size, 1)),
             xor=np.zeros(sigma.size, np.uint8), const=np.zeros(sigma.size, bool), key=np.int32(key))
    np.savez_compressed(work / "audiocpu_map.npz", **m)
    print(f"audiocpu: {sigma.size} output bytes, a permutation of the {n} input bytes at 0x10000; "
          f"0-0xFFFF repeat 0x10000-0x1FFFF: {bool(np.array_equal(sigma[:0x10000], sigma[0x10000:0x20000]))}")
    # A last, independent check: predict MAME's output for a fresh random image with the same key.
    rnd = np.random.default_rng(7).integers(0, 256, n).astype(np.uint8)
    rnd[rounds[0]] = 0
    need = (key - m1_key(rnd)) & 0xFFFF
    rnd[rounds[0][:need // 255]] = 255
    rnd[rounds[0][need // 255]] = need % 255
    got = run_probe(t, "predict", rnd, mame, base, work)["audiocpu"]
    bad = np.count_nonzero(apply(m, rnd, 8) != got)
    print(f"audiocpu: prediction for a fresh random image with the same key, {bad} bytes differ")
    if bad:
        sys.exit("audiocpu: model broken on the prediction check")


def read_set(t: Target, base: Path) -> dict[str, bytes]:
    want = {n for n, _ in t.files}
    found = {}
    for f in sorted(base.rglob("*")):
        if f.is_file() and zipfile.is_zipfile(f):
            with zipfile.ZipFile(f) as z:
                for n in z.namelist():
                    if n in want and n not in found:          # top level only: the parent set
                        found[n] = z.read(n)
        elif f.is_file() and f.name in want and f.parent.name == GAME:
            found.setdefault(f.name, f.read_bytes())
    missing = want - found.keys()
    if missing:
        sys.exit(f"missing in {base}: {sorted(missing)}")
    return found


def check(t: Target, base: Path, work: Path, dumps: Path) -> int:
    image = t.join(read_set(t, base))
    bad = 0
    for label in t.regions.values():
        m = dict(np.load(work / f"{label}_map.npz"))
        out = apply(m, image, t.bits)
        ref = np.frombuffer((dumps / f"{label}.bin").read_bytes(), t.dtype)
        diff = np.count_nonzero(out != ref)
        bad += diff
        print(f"{label}: learned map on the real set vs MAME's dump: {out.size - diff}/{out.size} units equal")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("action", choices=["learn", "check"])
    ap.add_argument("what", choices=sorted(TARGETS))
    ap.add_argument("--base", type=Path, default=Path(os.environ.get("PD_ROMS") or ROOT / "roms"))
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--dumps", type=Path, default=None)
    pd_tools = os.environ.get("PD_TOOLS")
    ap.add_argument("--mame", type=Path, default=Path(pd_tools or ROOT.parent / "tools", "mame", "mame.exe"))
    a = ap.parse_args()
    a.work.mkdir(parents=True, exist_ok=True)
    t = TARGETS[a.what]
    if a.action == "learn":
        (learn_keyed if t.name == "audio" else learn)(t, a.mame, a.base.resolve(), a.work.resolve())
        return 0
    return check(t, a.base.resolve(), a.work.resolve(), (a.dumps or a.base / "decrypted").resolve())


if __name__ == "__main__":
    sys.exit(main())
