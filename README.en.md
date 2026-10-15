# UUWay for Manjaro KDE

**A NetEase UU Remote Linux host for Manjaro KDE Plasma Wayland.** This repository adapts [GaryOAO/UUWay](https://github.com/GaryOAO/UUWay) to Manjaro KDE: the official Windows host runs under Wine, while KDE's screen-cast Portal, PipeWire, NVIDIA GPU encoding and native input services connect it to the Linux desktop.

> This is a **host**, not a viewer. It lets another computer or phone control this Linux machine; it cannot initiate a UU remote-control session to someone else's device. Use an official UU controller on the other device.

[简体中文](README.md) · [KDE adaptation notes](docs/manjaro-kde.md) · [AUR build and test record](docs/aur-manjaro-kde.md)

## Status and limits

**KDE support is experimental.** On October 14, 2026, an independent Manjaro KDE machine completed an AUR source build, pacman install, UU sign-in, screen and input authorization, and bridge startup. Separate diagnostics captured 2560 × 1600 DMA-BUF frames and successfully encoded and decoded a nonblack H.264 image. `uuway doctor` reported no failures or warnings. **An end-to-end session from another device has not yet been accepted on that machine.** The original workstation displayed the desktop, but black flicker on pointer movement still needs a live retest; audio has also produced harsh noise and is not guaranteed to work.

| Feature | Manjaro KDE status |
| --- | --- |
| UU host, sign-in and background bridge | Installed and running on the test machine; live viewer test pending |
| Physical-screen capture and NVIDIA H.264 encoding | Independent capture and encode/decode checks passed |
| Pointer, keyboard and Chinese IME | Local input services and Fcitx5 add-on running; live viewer test pending |
| Text clipboard, remote terminal and file transfer | Inherited from upstream; not fully accepted on KDE |
| Remote resolution/scale changes | KDE profile is read-only; change these in local System Settings |
| UU Super Screen (Windows virtual monitor) | Unsupported; share the existing physical monitor |
| Control at the login screen | Unsupported; a logged-in Plasma Wayland session is required |
| Control someone else's UU device from Linux | Unsupported; UUWay is not a viewer |

The current KDE profile requires **one active, non-mirrored, unrotated physical display**. The Wine Xvfb display runs UU internally; it is not the desktop to share. Choose the real monitor when granting permission. Multiple monitors, virtual displays and headless operation are not verified. See the [KDE adaptation notes](docs/manjaro-kde.md) for prior tests and limitations.

## Install

You need a Manjaro/Arch **Plasma Wayland** session, an NVIDIA GPU with NVENC and its driver, multilib enabled, and the official UU Remote **Windows installer**, obtained separately. The AUR build uses the host's pacman CUDA development headers. The verified test machine had CUDA 13.3 and system Wine 11.17. At runtime the package uses a separate SHA-256-verified WineHQ **11.0** under `/opt/uuway/wine-11.0`; it does not replace system Wine because the GPU bridge depends on this private protocol. The build downloads Wine archives and other sources and the installed package takes about 1.5 GB. See the [AUR documentation](docs/aur-manjaro-kde.md) for the full dependency and version boundary.

Install with an AUR helper:

```bash
yay -S uuway-git
```

Or build manually:

```bash
git clone https://aur.archlinux.org/uuway-git.git
cd uuway-git
makepkg -si
```

From a terminal in the **host machine's logged-in Plasma Wayland desktop**, run the wizard as your normal user (no `sudo` on `uuway setup`):

```bash
uuway doctor
uuway setup --installer /path/to/UURemote_Setup.exe
uuway doctor
```

Sign in in the UU window, select the physical monitor and save permission in KDE's screen-sharing dialog, then allow the separate input/clipboard request. Input rule installation may require administrator confirmation. The package contains **neither** the UU installer nor account data. Never copy a Wine prefix, login data or Portal grant from another machine.

The **UUWay Console** is available from the application menu. The KDE tray starts at desktop login and can start, restart or stop the local host. Use `uuway doctor` for status or `systemctl --user status uu-native-bridge uu-native-text` for service details. Upgrade with pacman/an AUR helper, then run `uuway refresh`. Ubuntu `.deb`/`apt` commands such as `uuway update install` and `rollback` **do not apply on Manjaro**; the source `./install.sh` is not the Manjaro installer either.

`uuway autologin on` configures upstream's **GDM** only. It does not configure SDDM, commonly used by KDE. If you need unattended availability after reboot, assess the security implications and configure desktop auto-login separately. UUWay is offline at the login screen.

### Screen capture delivers no frames

A successful screen-sharing grant does not prove PipeWire is delivering frames. On the test machine, only a dummy audio output remained and capture stopped delivering frames. Restarting WirePlumber restored real audio devices and capture. **This interrupts active media connections**; run it only when appropriate:

```bash
systemctl --user restart wireplumber.service
uuway setup --only portal --force portal
```

Choose the physical monitor again if asked. See the [AUR troubleshooting notes](docs/aur-manjaro-kde.md).

## Design and credits

UU's official Windows host continues to handle accounts, connections and bitrate negotiation. UUWay connects desktop capture, encoding and input to native Linux components. This fork adds a Plasma Wayland read-only display profile, an Arch-native AUR build and KDE tray integration. See the [design notes](docs/design.md) and [version review](docs/releases/4.42.0.2770-native-review.md).

Upstream: [GaryOAO/UUWay](https://github.com/GaryOAO/UUWay); earlier work: Lachlan Chen's [uu-remote-ubuntu-bridge](https://github.com/lachlanchen/uu-remote-ubuntu-bridge). Thanks to the original authors and to Wine, DXVK, PipeWire and their contributors. Ubuntu/GNOME users should follow the upstream instructions, **not** install an upstream `.deb` as this fork's Manjaro package.

The main project license is [AGPL-3.0](LICENSE); bundled third-party components retain their own licenses. This unofficial project is not affiliated with NetEase and does not distribute the official UU software.
