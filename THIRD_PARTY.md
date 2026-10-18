# Third parties

## Libraries integrated into the port and its tools

Each library is listed with its version, origin, license and how it is used. They are copied
together with their license file, unmodified except where the table says otherwise. The libraries
linked into the port (Musashi, z80.h, ymfm, stb_truetype and the menu fonts) arrive with the code
imported from the Metal Slug 3 port in Phase 1 and are listed here then.

| Library | Version | Origin | License | Use |
|---|---|---|---|---|
| Capstone | 5.0.7 | PyPI (`capstone`), github.com/capstone-engine/capstone | BSD-3-Clause | 68000 instruction decoder in the analysis tools. Not linked into the port. |
| NumPy | 2.5.4 | PyPI (`numpy`) | BSD-3-Clause | Graphics format conversion in the ROM tools. Not linked into the port. |

## Environment tools (not distributed with the repo)

The installer (`setup/setup.ps1`) downloads them into `tools\` from their official sources
(shared with the Metal Slug X and Metal Slug 3 ports). Only SDL3 and llvm-mingw's runtime will end up in a
release; the rest are only used for building and analysis.

| Tool | License | Use |
|---|---|---|
| SDL3 | zlib | Runtime window, input and audio. Linked dynamically: a release ships `SDL3.dll` with its license. |
| llvm-mingw | Apache-2.0 with LLVM exception, plus the mingw-w64 components | C compiler. Its C++ runtime (libc++, for ymfm) is linked statically into the executable; the LLVM exception requires no attribution for binaries. |
| CMake | BSD-3-Clause | Build |
| Ninja | Apache-2.0 | Build |
| Python (CPython) | PSF-2.0 | Analysis tools |
| Eclipse Temurin JDK 21 | GPL-2.0 with Classpath Exception | Required by Ghidra |
| Ghidra | Apache-2.0 | Disassembly and analysis |
| MAME | GPL-2.0+ (the project as a whole) | Oracle and debugger. Its source code is used only as hardware documentation reference and is never copied. |
| 7-Zip | LGPL-2.1 with unRAR restriction | Decompression |
| ImHex | GPL-2.0 | Hex editor |
| MinGit (Git for Windows) | GPL-2.0 | Version control |
| GitHub CLI | MIT | Publishing (repository and releases) |
