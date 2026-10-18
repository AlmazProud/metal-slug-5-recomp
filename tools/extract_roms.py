"""Rebuilds the MAME set (mslug3 + neogeo) from the DotEmu/GOG files.

Usage:
    python tools/extract_roms.py [--roms DIR] [--output DIR] [--maps DIR] [--mame EXE]

- Reads the mslug3_* files from --roms (%PD_ROMS% by default).
- Writes <output>/mslug3/* and <output>/neogeo/* (<roms>/mame by default).
- The GOG files hold MAME's regions already decrypted. The encrypted cartridge files (NEO-SMA
  program, CMC42 sprites) are rebuilt by inverting the maps that tools/probe_decryption.py
  learned from MAME by black-box probing (--maps, default <PD_ROOT>/analysis/phase0/probe):
  program_map.npz and sprites_map.npz. The maps are generated locally and never versioned.
- Gets the expected names and hashes from `mame -listxml` (MAME is the oracle), checks the
  CRC32 and SHA1 of each rebuilt file and prints a report.

The formats and transformations are documented in docs/ROM_MAP.md.
This script contains no ROM data: only transformations.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

import numpy as np

MB = 1 << 20
GAME = "mslug3"


# ---------------------------------------------------------------- formats (as in Metal Slug X)

def fix_dotemu_to_neogeo(d: bytes) -> bytes:
    """DotEmu 8x8 fix (4bpp, row-major, 4 bytes per row, low nibble = left pixel)
    to the Neo Geo S format (per 32-byte tile: 4 column groups of 8 bytes,
    one byte per row; groups in pixel order 4-5, 6-7, 0-1, 2-3)."""
    t = np.frombuffer(d, np.uint8).reshape(-1, 8, 4)        # tile, row, pixel pair
    group_of_pair = (2, 3, 0, 1)                            # pair k -> 8-byte group in the S tile
    out = np.empty((t.shape[0], 4, 8), np.uint8)            # tile, group, row
    for k, g in enumerate(group_of_pair):
        out[:, g, :] = t[:, :, k]
    return out.tobytes()


def sprites_dotemu_to_region(d: bytes) -> np.ndarray:
    """DotEmu sprite tiles (16x16, 4bpp, row-major, 8 bytes per row, low nibble = left pixel)
    to MAME's decrypted sprite region (even bytes: odd C ROM, planes 0-1; odd bytes: even C ROM,
    planes 2-3). Per 128-byte tile: left half (x 0-7) at 0x40-0x7F, right half at 0x00-0x3F,
    4 bytes per row: +0 plane 0, +1 plane 2, +2 plane 1, +3 plane 3; pixel x of the half is
    bit 7 - x (see docs/ROM_MAP.md)."""
    t = np.frombuffer(d, np.uint8).reshape(-1, 16, 8)
    px = np.empty((t.shape[0], 16, 16), np.uint8)
    px[:, :, 0::2] = t & 15
    px[:, :, 1::2] = t >> 4
    weights = (1 << np.arange(7, -1, -1)).astype(np.uint16)   # pixel 0 -> bit 7
    region = np.empty((t.shape[0], 128), np.uint8)
    for half, base in ((0, 0x40), (1, 0x00)):
        m = px[:, :, half * 8:(half + 1) * 8]
        for offset, plane in ((0, 0), (1, 2), (2, 1), (3, 3)):
            bits = ((m >> plane) & 1).astype(np.uint16) * weights
            region[:, base + offset: base + 64: 4] = bits.sum(axis=2).astype(np.uint8)
    return region.reshape(-1)


# ---------------------------------------------------------------- inverse of MAME's decryption

def program_encrypt(region: bytes, maps: Path) -> bytes:
    """MAME's 9 MB maincpu region (= mslug3_game_m68k) -> the 8 MB of P ROMs (pg1 + pg2).
    Output word i comes from input word sigma[i] with data line pi[b] for input bit b."""
    m = np.load(maps / "program_map.npz")
    sigma, pi, const = m["sigma"], m["pi"], m["const"]
    pi = pi[~const][0] if pi.ndim == 2 else pi                # the same for every word
    out_words = np.frombuffer(region, "<u2")[~const].astype(np.uint32)
    src = np.zeros_like(out_words)
    for b in range(16):
        src |= ((out_words >> np.uint32(pi[b])) & np.uint32(1)) << np.uint32(b)
    image = np.zeros(4 * MB, np.uint32)
    image[sigma[~const]] = src                                 # duplicated words are identical
    return image.astype("<u2").tobytes()


def sprites_encrypt(region: np.ndarray, maps: Path) -> np.ndarray:
    """MAME's decrypted sprite region -> the CMC42-encrypted C ROM image (region order).
    Learned model: output byte i = input byte sigma[i] XOR xor[i], data bits unchanged."""
    m = np.load(maps / "sprites_map.npz")
    if not np.all(m["pi"][0] == np.arange(8)):
        sys.exit("sprites_map.npz: unexpected data permutation")
    image = np.zeros(region.size, np.uint8)
    image[m["sigma"]] = region ^ m["xor"]
    return image


# ---------------------------------------------------------------- oracle (MAME)

def expected_from_mame(mame: Path) -> dict[str, dict]:
    xml = subprocess.run([str(mame), "-listxml", GAME], capture_output=True, check=True,
                         cwd=mame.parent).stdout
    expected = {}
    for m in ET.fromstring(xml).iter("machine"):
        for r in m.iter("rom"):
            if r.get("crc"):
                expected.setdefault(r.get("name"), {
                    "crc": r.get("crc"), "sha1": r.get("sha1"),
                    "size": int(r.get("size")), "region": r.get("region"), "machine": m.get("name")})
    return expected


# ---------------------------------------------------------------- rebuild

def rebuild(roms: Path, maps: Path) -> dict[str, tuple[str, bytes]]:
    """Returns {mame_name: (folder, data)}."""
    read = lambda n: (roms / n).read_bytes()
    out: dict[str, tuple[str, bytes]] = {}

    p = read("mslug3_game_m68k")                     # MAME's maincpu region, decrypted
    out["green.neo-sma"] = (GAME, p[0xC0000:0x100000])  # the NEO-SMA chip's own ROM, unencrypted
    pg = program_encrypt(p, maps)
    out["256-pg1.p1"] = (GAME, pg[:4 * MB])
    out["256-pg2.p2"] = (GAME, pg[4 * MB:])

    out["256-m1.m1"] = (GAME, read("mslug3_game_z80"))
    v = read("mslug3_adpcm")
    for k in range(4):
        out[f"256-v{k + 1}.v{k + 1}"] = (GAME, v[k * 4 * MB:(k + 1) * 4 * MB])

    t = read("mslug3_tiles")
    region = np.concatenate([sprites_dotemu_to_region(t[k * 16 * MB:(k + 1) * 16 * MB]) for k in range(4)])
    c = sprites_encrypt(region, maps).reshape(4, 16 * MB)
    for k in range(4):
        out[f"256-c{2 * k + 1}.c{2 * k + 1}"] = (GAME, c[k, 0::2].tobytes())
        out[f"256-c{2 * k + 2}.c{2 * k + 2}"] = (GAME, c[k, 1::2].tobytes())

    out["sp-u2.sp1"] = ("neogeo", read("mslug3_bios_m68k"))
    out["sfix.sfix"] = ("neogeo", fix_dotemu_to_neogeo(read("mslug3_bios_sfix")))
    out["000-lo.lo"] = ("neogeo", read("mslug3_zoom_table"))
    return out


# GOG does not include the Z80 BIOS of the MVS board. As on the Neo Geo AES (which has no SM1),
# the Z80 boots from the cartridge's M1: its first 128 KB (the size of sm1) are used.
# MAME accepts it with a checksum warning. Documented in docs/ROM_MAP.md.
SUBSTITUTES = {"sm1.sm1": ("neogeo", "256-m1.m1", 128 * 1024)}

# Known differences, documented in docs/ROM_MAP.md: GOG's system fix has 28 bytes changed.
KNOWN_DIFFERENT = {"sfix.sfix"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    pd_roms, pd_tools, pd_root = (os.environ.get(v) for v in ("PD_ROMS", "PD_TOOLS", "PD_ROOT"))
    ap.add_argument("--roms", type=Path, default=Path(pd_roms) if pd_roms else None)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--maps", type=Path, default=Path(pd_root, "analysis", "phase0", "probe") if pd_root else None)
    ap.add_argument("--mame", type=Path, default=Path(pd_tools, "mame", "mame.exe") if pd_tools else None)
    a = ap.parse_args()
    if not a.roms or not a.mame or not a.maps:
        ap.error("activate the environment (env.ps1) or pass --roms, --maps and --mame")
    for f in ("program_map.npz", "sprites_map.npz"):
        if not (a.maps / f).is_file():
            ap.error(f"{a.maps / f} is missing: run tools/probe_decryption.py program|graphics first")
    output = a.output or (a.roms / "mame")

    expected = expected_from_mame(a.mame)
    data = rebuild(a.roms, a.maps)
    substituted = set()
    for name, (folder, source, size) in SUBSTITUTES.items():
        real = output / folder / name
        if real.is_file() and f"{zlib.crc32(real.read_bytes()):08x}" == expected[name]["crc"]:
            continue                                  # the user supplied the genuine file
        data[name] = (folder, data[source][1][:size])
        substituted.add(name)

    print(f"{'file':<15} {'folder':<7} {'bytes':>9}  {'crc32':<8}  status")
    failures = 0
    for name, (folder, b) in data.items():
        target = output / folder
        target.mkdir(parents=True, exist_ok=True)
        (target / name).write_bytes(b)
        crc = f"{zlib.crc32(b):08x}"
        sha1 = hashlib.sha1(b).hexdigest()
        e = expected.get(name)
        if name in substituted:
            status = f"SUBSTITUTE ({SUBSTITUTES[name][1]}; MAME will warn about the checksum)"
        elif e is None:
            status = "NO REFERENCE IN MAME"
        elif crc == e["crc"] and sha1 == e["sha1"] and len(b) == e["size"]:
            status = "OK (CRC32+SHA1)"
        else:
            status = f"DIFFERENT (MAME expects crc {e['crc']})"
        failures += not (status.startswith("OK") or status.startswith("SUBSTITUTE")
                         or name in KNOWN_DIFFERENT)
        print(f"{name:<15} {folder:<7} {len(b):>9}  {crc}  {status}")

    missing = sorted(n for n, e in expected.items()
                     if n not in data and (e["machine"] == GAME and "bios" not in e["region"]
                                            or e["region"] in ("audiobios", "fixedbios", "spritegen:zoomy")))
    if missing:
        print("\nMAME also requires (GOG does not include them): " + ", ".join(missing))
    print(f"\nOutput: {output}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
