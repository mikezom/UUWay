# Manjaro KDE: native AUR build status

The intended AUR package is `uuway-git`: build the matching fork revision's
Windows DLLs and Linux workers from source on an Arch/Manjaro host, then install
the resulting files with pacman. An Ubuntu-built `.deb`, upstream 1.2.0 binary,
or a copy of another user's Wine prefix is **not** a native source build. There
is no published or verified `uuway-git` package yet. Do not submit a PKGBUILD
that only repackages the old `.deb` or silently picks up ignored `build/` files.

## Snapshot of the test host (2026-10-14)

Manjaro KDE Plasma Wayland, kernel `6.18.49-1-MANJARO`, NVIDIA RTX 3060 Laptop.
These are observations, **not** AUR version constraints or a guarantee of
compatibility on another machine. Check your own versions with `pacman -Q`.

| Component | Installed package/version | Build implication |
| --- | --- | --- |
| Plasma, KWin, KScreen | `plasma-desktop 6.7.4-1`, `kwin 6.7.4-7`, `kscreen 6.7.4-1` | KDE Portal, single physical output |
| Portal, PipeWire | `xdg-desktop-portal-kde 6.7.4-2`, `pipewire 1:1.6.8-1` | Screen capture and input consent |
| NVIDIA driver userspace | `nvidia-utils 610.57.04-1`, `lib32-nvidia-utils 610.57.04-1` | NVENC and `libcuda.so.1` at runtime |
| Fcitx | `fcitx5 5.1.22-1` | Native text add-on |
| Python and tray | `python 3.14.7-1`, `python-gobject 3.56.3-1`, `python-dbus 1.4.0-2`, `libappindicator 12.10.1-2` | Console/tray on KDE |
| System Wine | `wine 11.17-1` | **Not** the required Wine 11.0 protocol |
| Active Wine runtime | `~/.local/opt/uuway/wine-11.0/bin/wine` reports `wine-11.0` | The running `wineserver` resolves under this private tree; this is the version the bridge actually uses |
| CUDA | `cuda 13.3.1-1` | Its `cuda.h` declares `CUDA_VERSION 13030`; **not** the pinned 12.1 headers |
| C toolchain | `gcc 16.2.1+r23+gd564253eb6c8-1`, `glibc 2.44+r24+g16be1518495f-1`, `glslang 1:1.4.357.0-1` | Existing native builds used GCC 11 and need retesting |

The running capture executable references `cuCtxCreate_v2`, while the
installed CUDA 13.3 header maps `cuCtxCreate` to `cuCtxCreate_v4`. The local
NVIDIA driver exports both, but this does **not** mean rebuilding against the
new header reproduces the tested binary. `pacman -Q wine cuda` lists installed
system packages, not the Wine runtime or headers used for the running bridge.

The host did **not** have pacman-installed `xorg-server-xvfb`, `xclip`,
`lib32-freetype2` or `lib32-libpng`: its earlier local test used extracted,
user-private packages instead. Those local extracts are not package-managed
dependencies and must not be assumed to exist on another machine. The host
also lacked `mingw-w64-gcc`, `meson` and `ninja` at this snapshot.

## Required before publishing

1. Build against Wine **11.0** headers, import libraries and `winegcc` on
   Arch, with an installable, reproducible way to obtain them. Arch's historical
   repository has `wine-11.0-1-x86_64.pkg.tar.zst`, but extracting an old
   package is not yet a validated way to relocate and run Wine alongside the
   system version. The existing
   scripts hardcode `/opt/wine-stable/bin/winegcc` and download Wine 9
   development headers. The host's private Wine 11.0 installation has no
   installed development headers, while system Wine is 11.17. Merely changing
   `PATH` or symlinking system Wine does not solve protocol compatibility.
2. Supply **CUDA 12.1** driver API headers and link stub without overwriting
   the system CUDA 13.3 installation. Arch's historical CUDA 12.1 package is
   about 1.5 GB to download; a smaller, independently verified Arch-native
   header/stub source would make the AUR build more practical. The scripts expect
   `/usr/local/cuda/include/cuda.h` and link via the CUDA 12.1 stub; 13.3
   renames some driver symbols. Build inputs must be documented and fetched
   and verified in the package's source phase.
3. Build the patched DXVK 3.1, MinGW components, Wine backends, native
   capture workers, helpers and Fcitx module with the Arch toolchain. Current
   `scripts/prepare-dxvk-capture.py`, the DXVK cross file and build scripts
   select Ubuntu `.deb` cross-tools or hardcoded Wine/CUDA paths. Declare Arch
   build dependencies such as `mingw-w64-gcc`, `meson`, `ninja`, `glslang`,
   `pkgconf`, `vulkan-headers`, `pipewire`, `gst-plugins-base` and `fcitx5`;
   resolve compatibility before treating the build as supported.
4. Stage only the matching revision's outputs, following
   `packaging/deb_manifest.py` for runtime files. Test `makepkg` in a clean
   checkout without using the test host's ignored `build/` cache. Audit ELF
   dependencies on Manjaro, test `uuway doctor`, `uuway setup` with the
   official Windows installer, KDE consent, cursor motion, tray and removal.
   A successful `makepkg --printsrcinfo` is **not** a build test. Only then
   upload the PKGBUILD and `.SRCINFO` to AUR.

The existing package/update code still contains apt/dpkg-only paths. A native
Arch package must not enable `uuway update install` or `rollback`; upgrade
and removal must be handled by pacman. Do not use `./install.sh` or install a
`.deb` on Manjaro. Avoid publishing a recipe requiring the maintainer's
private paths or privileged Docker access. The user's official UU installer,
credentials, private Wine prefix and Portal tokens must never go into AUR or
the GitHub repository.

For the current single-output KDE runtime behavior and known audio limitation,
see [manjaro-kde.md](manjaro-kde.md). For installation on a different machine,
see [install-other-machines.md](install-other-machines.md).
