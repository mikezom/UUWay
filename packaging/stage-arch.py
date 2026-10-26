#!/usr/bin/python3
"""Stage runtime-only files into a pacman package tree (no Debian metadata)."""
import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'packaging'))
import deb_manifest  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', type=Path)
    parser.add_argument(
        '--legacy-build-layout',
        action='store_true',
        help='stage the single-backend build layout used by the Arch package',
    )
    args = parser.parse_args()
    destination = args.destination.resolve()
    if not destination.is_dir():
        parser.error('destination must exist')
    excluded = {'usr/share/lintian/overrides/uuway', 'usr/share/doc/uuway/copyright'}
    for source, target, mode in deb_manifest.files():
        if target in excluded:
            continue
        # Debian releases contain immutable NVIDIA and AMD trees under
        # build/backends.  The Manjaro package builds the local NVIDIA backend
        # into the historical root layout, so the root entries above are the
        # complete runtime for this package and backend-specific entries must
        # not be required here.
        if args.legacy_build_layout and source.startswith('build/backends/'):
            continue
        src = ROOT / source
        if not src.is_file():
            raise FileNotFoundError(src)
        dst = destination / target
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        dst.chmod(mode)
    for target, source in deb_manifest.COMMANDS.items():
        link = destination / target
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(source)


if __name__ == '__main__':
    main()
