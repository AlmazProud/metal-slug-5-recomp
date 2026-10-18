"""Decodes the NEO-SMA bank register from the black-box map made in MAME
(tools/mame/sma_bank_map.lua).

Usage:
    python tools/sma_banks.py MAP_TXT [--roms DIR]

For every 16-bit value written to the bank register, the map holds 16 samples of the P2 window
(16 bytes every 64 KB). Each window is located in MAME's program region (mslug3_game_m68k, whose
P2 part starts at 0x100000), which gives the offset of the bank the value selects. The script
then reports which bits of the value matter, the offset as a function of those bits, and checks
that function against all 65,536 values.
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("map", type=Path)
    pd_roms = os.environ.get("PD_ROMS")
    ap.add_argument("--roms", type=Path, default=Path(pd_roms) if pd_roms else None)
    a = ap.parse_args()
    if not a.roms:
        ap.error("activate the environment (env.ps1) or pass --roms")

    p = (a.roms / "mslug3_game_m68k").read_bytes()
    be = bytes(x for i in range(0, len(p), 2) for x in (p[i + 1], p[i]))   # 68000 view
    p2 = be[0x100000:]

    windows: dict[str, list[int]] = defaultdict(list)
    for line in a.map.read_text().splitlines():
        if line.startswith("TAPS"):
            continue
        v, sig = line.split()
        windows[sig].append(int(v, 16))

    offset_of: dict[int, int] = {}
    for sig, values in windows.items():
        samples = [bytes.fromhex(sig[k * 32:(k + 1) * 32]) for k in range(16)]
        found = []
        start = p2.find(samples[0])
        while start != -1:
            if start % 2 == 0 and all(p2[start + k * 0x10000:start + k * 0x10000 + 16] == samples[k]
                                      for k in range(16)):
                found.append(start)
            start = p2.find(samples[0], start + 1)
        if len(found) != 1:
            print(f"window of values {values[:4]}...: {len(found)} matches {[hex(f) for f in found[:4]]}")
            return 1
        for v in values:
            offset_of[v] = found[0]

    # Which bits of the value change the bank?
    relevant = [b for b in range(16) if any(offset_of[v] != offset_of[v ^ (1 << b)] for v in range(0x10000))]
    print(f"distinct banks: {len(windows)}; bits of the value that matter: {relevant}")
    # Bank offset for every combination of the relevant bits (others 0).
    table = {}
    for n in range(1 << len(relevant)):
        v = sum(((n >> i) & 1) << b for i, b in enumerate(relevant))
        table[n] = offset_of[v]
    # Is the offset a sum of per-bit contributions (linear)?
    contrib = [table[1 << i] - table[0] for i in range(len(relevant))]
    linear = all(table[n] == table[0] + sum(contrib[i] for i in range(len(relevant)) if (n >> i) & 1)
                 for n in table)
    print(f"offset with no relevant bit set: {table[0]:#x}")
    print("per-bit contribution: " + ", ".join(f"bit {b}: {c:+#x}" for b, c in zip(relevant, contrib)))
    print(f"offset = base + sum of contributions: {'yes, for all combinations' if linear else 'no'}")
    print("index (relevant bits, low first) -> P2 offset:")
    for n in sorted(table):
        print(f"  {n:3d} -> {table[n]:#08x}")
    bad = [v for v in range(0x10000)
           if offset_of[v] != table[sum(((v >> b) & 1) << i for i, b in enumerate(relevant))]]
    print(f"values checked against the table: 65536, mismatches: {len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
