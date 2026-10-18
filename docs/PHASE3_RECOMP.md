# Phase 3: analysis and recompilation of Metal Slug 5

**State:** in progress (started 2026-10-18).

## Plan

1. Where Metal Slug 5's 68000 runs in MAME (P1, the NEO-PVC window over P2, the BIOS, RAM), from
   traces of the attract and scripted runs.
2. Coverage and static analysis (`tools/coverage.py`, `tools/game_desc.py`, Ghidra cross-check):
   `docs/PHASE3_COVERAGE.md`.
3. Recompilation with `tools/recomp68k` (P1 and the BIOS, as for Metal Slug 3). If code runs from
   the P2 banks, the dispatcher is the user's decision. `pd_recompiled_program` must read the
   decrypted reference files instead of a PC release's `<id>_game_m68k`.
4. Tests: lockstep per run and image, RAM and palette against MAME for the recompiled build. The
   audio is deferred (Phase 2) and stays out of the pass criteria.
5. A game recorded by the user (`grabar_partida.bat`) for coverage and verification.

The distributable build stays interpreter-only (`-DPD_RECOMPILED=OFF`); the recompiled build is
the development and verification target, as in Metal Slug 3.
