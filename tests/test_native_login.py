"""Native login must preserve existing loaders and clean its own partial setup."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_login', ROOT / 'scripts/uu-native-login.py')
login = importlib.util.module_from_spec(spec)
spec.loader.exec_module(login)


class NativeLoginTests(unittest.TestCase):
    def test_guest_configuration_does_not_count_as_logged_in(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            settings = prefix / 'drive_c/users/zyk/AppData/Local/GameViewer'
            settings.mkdir(parents=True)
            (settings / 'setting_guest_1.ini').touch()
            self.assertFalse(login.logged_in(prefix))
            (settings / 'setting_account.ini').touch()
            self.assertTrue(login.logged_in(prefix))

    def test_tray_quit_is_a_server_missing_past_the_restart_grace(self):
        watcher = login.QuitWatcher()
        grace = login.SERVER_GONE_SECONDS
        self.assertFalse(watcher.quit(False, 0), 'a server that never started is not a quit')
        self.assertFalse(watcher.quit(False, grace + 1))
        self.assertFalse(watcher.quit(True, 100))
        self.assertFalse(watcher.quit(False, 101))
        self.assertFalse(watcher.quit(True, 101 + grace - 1), 'Healthd restarted it within the grace')
        self.assertFalse(watcher.quit(False, 200))
        self.assertFalse(watcher.quit(False, 200 + grace - 1))
        self.assertTrue(watcher.quit(False, 200 + grace))

    def test_busy_prefix_is_rejected_before_creating_login_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prefix = root / 'prefix'
            prefix.mkdir(mode=0o700)
            with patch.object(login.trial.bundle_tools, 'verify'), \
                    patch.object(login.trial, 'prefix_processes', return_value=[{'pid': 1}]), \
                    patch.object(login.subprocess, 'Popen') as launcher:
                with self.assertRaisesRegex(RuntimeError, 'busy'):
                    login.run(prefix, root / 'bundle', root / 'state')
            launcher.assert_not_called()
            self.assertEqual(list((root / 'state').iterdir()), [])

    def test_existing_loader_is_preserved_and_partial_links_are_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prefix = root / 'prefix'
            prefix.mkdir(mode=0o700)
            app = prefix / 'drive_c/Program Files/Netease/GameViewer/bin'
            app.mkdir(parents=True)
            existing = app / 'existing.dll'
            existing.write_bytes(b'original')
            bundle = root / 'bundle'
            (bundle / 'runtime').mkdir(parents=True)
            for name in ('bootstrap.exe', 'winlogon.exe'):
                (bundle / 'runtime' / name).write_bytes(b'MZ')
            with patch.object(login.trial.bundle_tools, 'verify'), \
                    patch.object(login.trial, 'prefix_processes', return_value=[]), \
                    patch.object(login.trial.bundle_tools, 'INPUTS',
                                 {'app/bin/new.dll': '', 'app/bin/existing.dll': ''}), \
                    patch.object(login.subprocess, 'Popen') as launcher:
                with self.assertRaisesRegex(RuntimeError, 'existing loader'):
                    login.run(prefix, bundle, root / 'state')
            launcher.assert_not_called()
            self.assertEqual(existing.read_bytes(), b'original')
            self.assertFalse((app / 'new.dll').is_symlink())
            self.assertEqual(len(list((root / 'state').glob('login-*/cleanup.json'))), 1)


if __name__ == '__main__':
    unittest.main()
