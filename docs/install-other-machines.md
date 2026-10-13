# Install this fork on another computer

The source in this fork includes the experimental KDE capture fixes and the
UUWay tray. An upstream 1.2.0 release binary does **not** include changes made
in this fork. Build from the desired commit; do not mix an older release's
native capture or Wine DLL binaries with this checkout. UU's Windows installer
must be obtained separately from the official provider.

Do not copy your original computer's Wine prefix, account settings, Portal
restore tokens, private keys, or `~/.local/state/uurb` to the new computer.
Each desktop needs its own UU login and screen/input authorization.

## Ubuntu 24.04, GNOME Wayland

Use a logged-in graphical Wayland session and an NVIDIA GPU with NVENC and the
proprietary driver. On the target computer, with Docker available, clone this
fork and build its package in an Ubuntu 24.04 container:

```bash
git clone https://github.com/zyk-miao/UUWay.git
cd UUWay
packaging/build-deb.sh
sudo apt install ./build/deb/uuway_*_amd64.deb
uuway setup --installer "$HOME/Downloads/UURemote_Setup.exe"
uuway doctor
```

Run `uuway setup` as your normal desktop user, **not** with `sudo`. Sign in to
the UU window, approve the screen-sharing dialog (select the physical monitor
and remember the permission), and approve the separate input/text dialog.
The console is available from the application menu; the tray starts at desktop
login. The bridge only comes online after the desktop session has logged in.
This is a build from the fork's source, not an automatically published or
signed release. Review the code and package before installation.

Without Docker, see [build.md](build.md) for Ubuntu source-build requirements.

## Manjaro KDE Wayland (experimental)

There is **no ready-to-install Manjaro package or one-command installer** in
this fork. Ubuntu `.deb` files and `./install.sh` must not be run as Manjaro
installers. The tested KDE profile requires one active, unmirrored, unrotated
physical display at origin (0, 0), a working KDE screen-cast Portal, NVIDIA
NVENC, `/dev/uinput` access, and a WineHQ **11.0** runtime. The system's newer
Wine version cannot be silently substituted. KDE's virtual display is not a
replacement for this physical-output profile. See
[native AUR build status and host package versions](aur-manjaro-kde.md) before
trying to package this for a different Manjaro computer. The existing Ubuntu
container procedure below documents the earlier manual trial; it is **not**
the proposed Arch-native AUR build.

Before attempting a fresh KDE installation:

1. Clone this fork on the target and check its environment from the logged-in
   Plasma Wayland desktop with `/usr/bin/python3 scripts/uuway_cli.py doctor`,
   `kscreen-doctor -j` and `nvidia-smi -L`.
2. Build the **same commit's** native components in the documented Ubuntu 24.04
   build container (`packaging/build-deb.sh`), then stage those artifacts into
   the matching checkout on the Manjaro machine; verify their ELF dependencies
   and the NVIDIA driver libraries there. Do not install the resulting Debian
   package via pacman or dpkg on Manjaro. See [manjaro-kde.md](manjaro-kde.md)
   for the Wine 11.0, dependencies and native artifact requirements.
3. Set up the Manjaro-specific Xvfb/xclip and 32-bit Wine dependencies and
   input rule; check their permissions. Install the console/menu identity with
   `/usr/bin/python3 scripts/install-uu-settings.py` **before** authorizing
   screen sharing. Do not enable the GNOME/Mutter display guardian on KDE.
4. Once all prerequisites are verified, use the target machine's own official
   Windows UU installer and run `/usr/bin/python3 scripts/uuway_cli.py setup
   --installer /path/to/UURemote_Setup.exe` as the logged-in user. Sign in and
   grant screen/input access **on that machine**. Check the resulting service
   with `/usr/bin/python3 scripts/uuway_cli.py doctor`.

The tested Manjaro host needed private Wine 11.0, compatible native libraries
and additional integration work; this procedure is not yet validated as a
portable installation. Avoid copying its private build cache or installed
prefix to another computer. See [manjaro-kde.md](manjaro-kde.md) for the
hardware-specific test results and known audio limitation.
