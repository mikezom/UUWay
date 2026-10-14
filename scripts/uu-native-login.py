#!/usr/bin/python3
"""Open UU login with temporary native loaders and restore them on exit."""
import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('login_trial', ROOT / 'scripts/uu-native-trial.py')
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)


def logged_in(prefix):
    return any(not path.name.startswith('setting_guest_') for path in
               prefix.glob('drive_c/users/*/AppData/Local/GameViewer/setting_*.ini'))


def run(prefix, bundle, state_parent, wait_for_user=False):
    prefix = prefix.resolve()
    bundle = bundle.resolve()
    trial.private_directory(prefix)
    trial.bundle_tools.verify(bundle)
    state_parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    trial.private_directory(state_parent)
    if trial.prefix_processes(prefix):
        raise RuntimeError('Quit UU before opening native login: the Wine prefix is busy')
    directory = Path(tempfile.mkdtemp(prefix='login-', dir=state_parent))
    env = trial.wine_locale(dict(os.environ, WINEPREFIX=str(prefix), WINELOADER=trial.WINE,
                                WINEDEBUG='-all', UURB_NATIVE_BOOTSTRAP='1',
                                WINEDLLOVERRIDES='mscoree,mshtml=', QT_OPENGL='software',
                                QT_ANGLE_PLATFORM='warp', __GLX_VENDOR_LIBRARY_NAME='nvidia'))
    for name in ('UURB_NATIVE_INPUT_ENABLED', 'QT_IM_MODULE', 'QT_LINUX_ACCESSIBILITY_ALWAYS_ON',
                 'QT_WAYLAND_RECONNECT', 'SDL_IM_MODULE'):
        env.pop(name, None)
    app = prefix / 'drive_c/Program Files/Netease/GameViewer'
    token = 'UURB-NATIVE-' + uuid.uuid4().hex
    arguments = [str(directory / 'bootstrap.exe'), '--run', str(directory / 'capture.sock'),
                 trial.winpath(bundle / 'dxvk.conf'), trial.winpath(app / 'GameViewer.exe'), token]
    created, launcher = [], None
    stopping = False

    def stop(*unused):
        nonlocal stopping
        stopping = True

    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        for source, name in (('runtime/bootstrap.exe', 'bootstrap.exe'),
                             ('runtime/winlogon.exe', 'winlogon.exe')):
            shutil.copy2(bundle / source, directory / name)
        for name in trial.bundle_tools.INPUTS:
            if name.startswith('app/bin/'):
                path = app / 'bin' / Path(name).name
            elif name.startswith('system32/'):
                path = prefix / 'drive_c/windows/system32' / Path(name).name
            else:
                continue
            if path.exists() or path.is_symlink():
                raise RuntimeError('Refusing an existing loader: ' + path.name)
            target = (bundle / name).resolve()
            path.symlink_to(target)
            info = path.lstat()
            created.append((path, target, (info.st_dev, info.st_ino)))
        with (directory / 'wine.log').open('w') as log:
            launcher = subprocess.Popen([trial.WINE, *arguments], env=env, cwd=app,
                                        stdout=log, stderr=log, start_new_session=True)
        print('请在 UU 窗口中登录，登录成功后安装向导会自动继续。', flush=True)
        started = time.monotonic()
        restored = False
        while not stopping and time.monotonic() - started < 3600:
            if not restored and time.monotonic() - started >= 8:
                subprocess.run([trial.WINE, str(ROOT / 'build/native-presenter/uu-show-login.exe')],
                               env=env, timeout=15, check=True)
                restored = True
                if wait_for_user:
                    input('登录完成后从 UU 托盘完全退出，然后按回车继续…')
                    break
            if logged_in(prefix) or launcher.poll() is not None:
                break
            time.sleep(1)
        success = logged_in(prefix) and not stopping
    finally:
        failures = trial.cleanup_trial(launcher, None, env, directory, arguments, token, created)
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        if failures == ['stop_owned_prefix'] and not trial.prefix_processes(prefix):
            if {'event': 'configuration_removed', 'code': 0} in trial.boot_events(directory / 'wine.log'):
                failures = []
        if failures:
            raise RuntimeError('Native login cleanup failed; inspect ' + str(directory / 'cleanup.json'))
    return 0 if success else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', type=Path, required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--state-parent', type=Path, required=True)
    parser.add_argument('--wait-for-user', action='store_true')
    args = parser.parse_args()
    return run(args.prefix, args.bundle, args.state_parent, args.wait_for_user)


if __name__ == '__main__':
    raise SystemExit(main())
