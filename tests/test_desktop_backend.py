"""Read-only Plasma topology and service policy checks."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('desktop_backend', ROOT / 'scripts/desktop_backend.py')
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)


def fixture():
    return dict(outputs=[dict(name='eDP-1', connected=True, enabled=True, currentModeId='1',
                              modes=[dict(id='1', size=dict(width=1920, height=1080))],
                              size=dict(width=1920, height=1080), pos=dict(x=0, y=0),
                              scale=1.25, rotation=1, replicationSource=0)])


class PlasmaTests(unittest.TestCase):
    def test_user_wine_is_used_only_when_system_wine_is_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            system, local = Path(directory) / 'system', Path(directory) / 'local'
            system.mkdir()
            local.mkdir()
            self.assertEqual(backend.wine_bin_directory(system, local), system)
            (local / 'wine').touch()
            self.assertEqual(backend.wine_bin_directory(system, local), local)
            (system / 'wine').touch()
            self.assertEqual(backend.wine_bin_directory(system, local), system)

    def test_session_detection(self):
        self.assertTrue(backend.plasma_wayland(dict(XDG_SESSION_TYPE='wayland', XDG_CURRENT_DESKTOP='KDE')))
        self.assertFalse(backend.plasma_wayland(dict(XDG_SESSION_TYPE='x11', XDG_CURRENT_DESKTOP='KDE')))
        self.assertFalse(backend.plasma_wayland(dict(XDG_SESSION_TYPE='wayland', XDG_CURRENT_DESKTOP='GNOME')))

    def test_single_output_returns_stable_generation_and_pixel_dimensions(self):
        data = fixture()
        first = backend.plasma_topology(data)
        self.assertEqual(first, backend.plasma_topology(data))
        self.assertEqual(first['connectors'], ['eDP-1'])
        self.assertEqual(first['modes'], [dict(width=1920, height=1080)])
        self.assertEqual(first['layout'][0]['scale'], 1.25)
        data['outputs'][0]['currentModeId'] = '2'
        data['outputs'][0]['modes'].append(dict(id='2', size=dict(width=1920, height=1080)))
        self.assertNotEqual(first['generation'], backend.plasma_topology(data)['generation'])

    def test_unsafe_layouts_are_rejected(self):
        changes = [lambda d: d['outputs'].append(dict(d['outputs'][0])),
                   lambda d: d['outputs'][0].update(rotation=2),
                   lambda d: d['outputs'][0]['pos'].update(x=1),
                   lambda d: d['outputs'][0].update(size=dict(width=1919, height=1080)),
                   lambda d: d['outputs'][0].update(scale=float('nan')),
                   lambda d: d['outputs'][0].update(connected=False),
                   lambda d: d['outputs'][0].update(replicationSource=1)]
        for change in changes:
            data = fixture()
            change(data)
            with self.subTest(change=change), self.assertRaises(RuntimeError):
                backend.plasma_topology(data)

    def test_runtime_uses_kscreen_only_on_plasma(self):
        spec = importlib.util.spec_from_file_location('kde_trial', ROOT / 'scripts/uu-native-trial.py')
        trial = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(trial)
        with patch.object(trial, 'plasma_wayland', return_value=True), \
                patch.object(trial, 'current_plasma_topology', return_value=backend.plasma_topology(fixture())) as query:
            self.assertEqual(trial.native_topology()['connectors'], ['eDP-1'])
            query.assert_called_once_with()
