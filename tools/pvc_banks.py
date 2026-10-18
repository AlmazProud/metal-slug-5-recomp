"""Checks a model of the NEO-PVC bank registers against the black-box map made in MAME
(tools/mame/pvc_bank_map.lua). Adapted from the Metal Slug 3 port's sma_banks.py (MIT,
Copyright (c) 2026 AlmazProud).

Usage:
    python tools/pvc_banks.py MAP_TXT [--maincpu FILE]

For every value written to a bank register (the other one held, as the map says), the map holds
16 samples of the P2 window (8 bytes every 64 KB, 68000 order). Model being checked: the two
registers form a 32-bit value V = 0x2FFFF2:0x2FFFF0, and the window 0x200000-0x2FFFFF shows MAME's
decrypted program region (`maincpu.bin`, dumped with tools/mame/dump_region.lua into
<workspace>/roms/decrypted, file byte order) from the byte offset 0x100000 + (V >> 8); bytes past
the end of the region read 0xFF. With an odd offset the 68000's words straddle two of the
region's words. Every sample of every value is predicted and compared; the script lists the
values (as ranges) where the model fails.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HOLD = {"2FFFF0": 0x0000, "2FFFF2": 0x1000}      # pvc_bank_map.lua's defaults


def ranges(vs: list[int]) -> str:
    if not vs:
        return "none"
    out, start = [], vs[0]
    for a, b in zip(vs, vs[1:] + [None]):
        if b != a + 1:
            out.append(f"{start:#06x}-{a:#06x}")
            if b is not None:
                start = b
    return ", ".join(out[:8]) + (f" ... ({len(out)} ranges)" if len(out) > 8 else "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("map", type=Path)
    roms = Path(os.environ.get("PD_ROMS") or ROOT / "roms")
    ap.add_argument("--maincpu", type=Path, default=roms / "decrypted" / "maincpu.bin")
    a = ap.parse_args()

    region = a.maincpu.read_bytes()
    padded = region + b"\xff" * (2 * 1024 * 1024)

    def window(offset: int, k: int) -> str:
        o = offset + k * 0x10000
        raw = padded[o:o + 8]
        return bytes(x for i in range(0, 8, 2) for x in (raw[i + 1], raw[i])).hex().upper()

    fails: dict[str, list[int]] = {}
    seen: dict[str, int] = {}
    for line in a.map.read_text().splitlines():
        reg, v, sig = line.split()
        regs = dict(HOLD)
        regs[reg] = int(v, 16)
        value = (regs["2FFFF2"] << 16) | regs["2FFFF0"]
        offset = 0x100000 + (value >> 8)
        seen[reg] = seen.get(reg, 0) + 1
        pred = "".join(window(offset, k) for k in range(16))
        if pred != sig:
            fails.setdefault(reg, []).append(int(v, 16))
    for reg in sorted(seen):
        f = fails.get(reg, [])
        print(f"register {reg} (others held at {HOLD}): {seen[reg]} values, {seen[reg] - len(f)} as the model "
              f"predicts; failures: {ranges(f)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
