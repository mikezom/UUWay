# Manjaro KDE: native AUR build

`packaging/aur/PKGBUILD` builds the DLLs, workers, DXVK patch, helpers and
Fcitx add-on from source on Arch/Manjaro. It stages the same runtime file list
as the Debian package, without Debian packaging or installing files from the
maintainer's machine. **AUR publication and clean `makepkg` verification are
pending.** Do not submit or install an unverified package.

## Build dependencies and version boundary

The native compiler, MinGW, Meson, Ninja, Vulkan/GLSL, Fcitx and CUDA headers
come from pacman. The tested build uses the system CUDA 13.3 headers and stub
at `/opt/cuda`; CUDA 12.1 retains its original three-argument context API.
The compatibility shim selects CUDA 13.3's four-argument API at compile time.
The resulting binary references the API provided by the installed NVIDIA
driver; building successfully does not guarantee all NVENC/display operations
on another GPU/driver. Verify the driver before using UUWay.

The native Wine GPU adapter uses Wine **11.0** private server protocol 930.
The system Wine 11.17 cannot be substituted for that runtime. `makepkg` obtains
the SHA-256-verified official WineHQ 11.0 amd64 `.deb` as a build input and
places its Wine files under `/opt/uuway/wine-11.0` inside the pacman package.
This is **not** an Ubuntu build or a `.deb` installation, and does not replace
`/usr/bin/wine`. The Arch Wine package supplies generated development headers
for building; pinned Wine 11.0 source provides its private server header.
DXVK and its submodules are also fixed to reviewed revisions. No official UU
installer, account credentials, Wine prefix or Portal tokens are packaged.

## Build machine (2026-10-14)

An independent Manjaro KDE test machine at `192.168.31.37` has an NVIDIA
RTX 4090 Laptop GPU, driver `610.57.04`, Wine `11.17-1`, CUDA `13.3.1-1`,
Fcitx5 `5.1.22-1` and GCC `16.2.1`. We installed Arch build dependencies
`mingw-w64-gcc`, `meson`, `ninja` and `vulkan-headers`. Its native source build
completed, the CUDA context API was exercised against the real driver, and
the staged runtime produced a verified 26-component user bundle with no
unresolved ELF dependencies. This does **not** establish live UU/NVENC/Portal
acceptance: the machine does not yet have the official UU Windows installer
or a logged-in UU prefix.

On the original workstation (RTX 3060 Laptop, same Wine and CUDA pacman
versions), the running bridge still uses a separate private Wine 11.0 and
the older CUDA 12.1-built capture binary. Do not confuse installed toolkit
versions with the versions used to build a running executable.

## Installation and testing

From this repository, `packaging/aur/PKGBUILD` is the reviewable recipe.
After a verified AUR publication, run `makepkg -si` in the cloned AUR package
directory as an ordinary user. Then install the official Windows UU Remote
host and complete KDE screen-sharing consent on the **target machine**:

```bash
uuway doctor
uuway setup --installer /path/to/UURemote_Setup.exe
uuway doctor
```

`setup` may require interactive desktop login and consent; do not provide UU
credentials to the package builder. Keep one physical output active during
initial tests. AUR upgrades are handled by pacman/AUR tools followed by
`uuway refresh`; `uuway update install`/`rollback` remain disabled on Arch.
Before publishing, run clean `makepkg` and inspect the built package and
runtime on the target machine. The builder should not rely on ignored `build/`
files or an installed Docker image. See [manjaro-kde.md](manjaro-kde.md) for
known KDE and audio limitations.
