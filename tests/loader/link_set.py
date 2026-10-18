"""Test fixture: a folder with only a MAME set, linked (or copied) from the user's ROM folder.

Usage: python tests/loader/link_set.py ROMS DEST FILE [FILE...]
Each FILE (relative to ROMS, e.g. mslug5.zip or neogeo/sp-u2.sp1) ends up at DEST/FILE, as a hard
link when the file system allows it. DEST is emptied first. Nothing leaves the build folder.
"""
import os
import shutil
import sys
from pathlib import Path


def main() -> int:
    roms, dest, files = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3:]
    shutil.rmtree(dest, ignore_errors=True)
    for f in files:
        src, out = roms / f, dest / f
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(src, out)
        except OSError:
            shutil.copyfile(src, out)
    print(f"{len(files)} files in {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
