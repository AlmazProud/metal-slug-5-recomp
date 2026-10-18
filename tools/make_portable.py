"""Builds a portable copy of the games for personal use (e.g. a USB drive): nothing is installed
and nothing is written to the computer it runs on.

Usage:
  python tools/make_portable.py --out E:\\ [--build repo/build]
                                [--mslug3 <root>/roms] [--mslugx <root>/../roms]

For each game whose files are given, <out>/Metal Slug/<game>/ gets the executable, SDL3.dll, the
licenses, a "game" folder with the user's own copy of the PC release files (copied from the given
folder: the DotEmu files only, not MAME sets) and an empty "save" folder. With "save" next to the
executable the port runs in portable mode: settings, SRAM, saved games and the title logo go there.

The output holds the user's game files: it is for the user only, never published or committed.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parent

GAMES = {"mslug3": "Metal Slug 3", "mslugx": "Metal Slug X"}

README = """{title} - portable native port

Run {exe}. Settings, saved games and the battery RAM are kept in the "save" folder next to it,
so nothing is installed or written on the computer. Your game files are in the "game" folder.

Keys: Esc menu - F5/F9 save/load state - F11 fullscreen - F12 screenshot - F3 debug panel.
Player 1: arrows, Z shoot, X jump, C grenade, 1 start, 5 coin, B autofire.
Gamepads work out of the box (Guide or Back+Start opens the menu, Share takes a screenshot).
Screenshots go to the "screenshots" folder inside "save".

--

Ejecuta {exe}. Los ajustes, las partidas guardadas y la memoria de la placa se guardan en la
carpeta "save" junto a el: no se instala ni se escribe nada en la computadora. Tus archivos del
juego estan en la carpeta "game".

Teclas: Esc menu - F5/F9 guardar/cargar partida - F11 pantalla completa - F12 captura -
F3 panel de depuracion. Jugador 1: flechas, Z disparar, X saltar, C granada, 1 start,
5 moneda, B disparo automatico. Los mandos funcionan sin configurar (Guide o Back+Start abre
el menu; Share saca una captura). Las capturas van a la carpeta "screenshots" dentro de "save".

{title} is (c) SNK CORPORATION. Unofficial fan project, not affiliated with or endorsed by SNK.
"""


def copy_game(game: str, files: Path, build: Path, out: Path) -> int:
    exe = build / "src" / f"{game}.exe"
    dll = build / "src" / "SDL3.dll"
    for f in (exe, dll):
        if not f.is_file():
            print(f"missing {f}: build first", file=sys.stderr)
            return 1
    data = sorted(p for p in files.iterdir() if p.is_file() and p.name.startswith(f"{game}_"))
    if not data:
        print(f"no {game}_* files in {files}", file=sys.stderr)
        return 1
    dest = out / "Metal Slug" / GAMES[game]
    (dest / "game").mkdir(parents=True, exist_ok=True)
    (dest / "save").mkdir(exist_ok=True)
    shutil.copy2(exe, dest)
    shutil.copy2(dll, dest)
    for name in ("LICENSE", "THIRD_PARTY.md"):
        if (REPO / name).is_file():
            shutil.copy2(REPO / name, dest / (name + ".txt" if "." not in name else name))
    if (REPO / "licenses").is_dir():
        shutil.copytree(REPO / "licenses", dest / "licenses", dirs_exist_ok=True)
    for f in data:
        target = dest / "game" / f.name
        if not target.exists() or target.stat().st_size != f.stat().st_size:
            shutil.copy2(f, target)
    (dest / "README.txt").write_text(README.format(title=GAMES[game], exe=exe.name), encoding="utf-8")
    size = sum(p.stat().st_size for p in dest.rglob("*") if p.is_file())
    print(f"{GAMES[game]}: {dest} ({size / 2**20:.0f} MB, {len(data)} game files)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True, help="destination (a drive or a folder)")
    ap.add_argument("--build", type=Path, default=REPO / "build")
    ap.add_argument("--mslug3", type=Path, default=ROOT / "roms", help="folder with the mslug3_* files")
    ap.add_argument("--mslugx", type=Path, default=ROOT.parent / "roms", help="folder with the mslugx_* files")
    a = ap.parse_args()
    if REPO in a.out.resolve().parents or a.out.resolve() == REPO:
        print("the output must be outside the repository", file=sys.stderr)
        return 2
    r = 0
    for game in GAMES:
        r |= copy_game(game, getattr(a, game), a.build, a.out)
    return r


if __name__ == "__main__":
    sys.exit(main())
