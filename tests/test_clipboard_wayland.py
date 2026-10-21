"""Native clipboard transfers on an isolated headless KWin and two Xvfb servers.

No connection to the physical desktop or its session bus is made.
"""
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import tempfile
import time
import unittest

from tests.test_clipboard_bridge import ROOT, start_xvfb


@unittest.skipUnless(all(shutil.which(tool) for tool in
                        ('kwin_wayland', 'dbus-run-session', 'Xvfb', 'xclip', 'wayland-scanner')),
                     'needs KWin, Wayland development tools, Xvfb and xclip')
class NativeWaylandClipboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix='uurb-native-clipboard-')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.root = Path(cls.directory.name)
        cls.build = cls.root / 'build'
        subprocess.run(['bash', str(ROOT / 'scripts/build-clipboard-bridge.sh'), str(cls.build)], check=True)
        cls.source = cls.build / 'source'
        flags = subprocess.check_output(['pkg-config', '--cflags', '--libs', 'wayland-client'], text=True).split()
        generated = ROOT / 'build/clipboard-protocol'
        subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-I', str(generated),
                        '-o', str(cls.source), str(ROOT / 'tests/fixtures/wayland_clipboard_source.c'),
                        str(generated / 'ext-data-control-v1.c'), *flags], check=True)
        cls.environment = dict(os.environ, XDG_RUNTIME_DIR=str(cls.root),
                               XDG_CONFIG_HOME=str(cls.root / 'config'),
                               XDG_DATA_HOME=str(cls.root / 'data'),
                               XDG_CACHE_HOME=str(cls.root / 'cache'),
                               WAYLAND_DISPLAY='uuway-test', QT_QPA_PLATFORM='offscreen',
                               LIBGL_ALWAYS_SOFTWARE='1', UURB_CLIPBOARD_WAYLAND='1',
                               DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
        cls.environment.pop('XAUTHORITY', None)
        cls.environment.pop('WAYLAND_SOCKET', None)
        cls.compositor_log = tempfile.TemporaryFile()
        cls.addClassCleanup(cls.compositor_log.close)
        cls.compositor = subprocess.Popen(
            ['dbus-run-session', '--', 'kwin_wayland', '--virtual', '--socket', 'uuway-test',
             '--width', '320', '--height', '240', '--no-lockscreen', '--no-global-shortcuts',
             '--no-kactivities'], env=cls.environment, stdout=cls.compositor_log,
            stderr=cls.compositor_log, start_new_session=True)
        cls.addClassCleanup(cls.stop_compositor)
        deadline = time.monotonic() + 15
        while not (cls.root / 'uuway-test').exists():
            if cls.compositor.poll() is not None or time.monotonic() > deadline:
                cls.compositor_log.seek(0)
                raise RuntimeError(cls.compositor_log.read().decode(errors='replace'))
            time.sleep(.05)

    @classmethod
    def stop_compositor(cls):
        try:
            os.killpg(cls.compositor.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        cls.compositor.wait(timeout=5)

    def setUp(self):
        self.processes = []
        self.uu_server, self.uu = start_xvfb(self.environment)
        self.desktop_server, self.desktop = start_xvfb(self.environment)
        self.log = tempfile.TemporaryFile()
        self.bridge = subprocess.Popen(
            [str(self.build / 'uu-clipboard-bridge'), self.uu, self.desktop],
            env=self.environment, stdout=subprocess.DEVNULL, stderr=self.log,
            start_new_session=True)
        self.addCleanup(self.stop)
        self.wait_for(lambda: b'native Wayland clipboard connected' in self.read_log())

    def stop(self):
        os.killpg(self.bridge.pid, signal.SIGTERM)
        self.bridge.wait(timeout=5)
        for process in reversed(self.processes):
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()
        for process in (self.uu_server, self.desktop_server):
            process.terminate()
            process.wait(timeout=5)
        self.log.close()

    def read_log(self):
        self.log.seek(0)
        return self.log.read()

    def wait_for(self, predicate, seconds=4):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(.02)
        self.fail(self.read_log().decode(errors='replace'))

    def copy_native(self, formats, delay=0):
        arguments = []
        for index, (mime, value) in enumerate(formats.items()):
            path = self.root / f'payload-{len(self.processes)}-{index}'
            path.write_bytes(value)
            arguments.extend((mime, str(path)))
        process = subprocess.Popen([str(self.source), *arguments],
                                   env=dict(self.environment, UURB_TEST_SEND_DELAY_MS=str(delay)),
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        self.processes.append(process)
        self.assertTrue(select.select([process.stdout], [], [], 3)[0], 'native source not ready')
        self.assertEqual(process.stdout.readline(), b'ready\n')

    def paste(self, target='UTF8_STRING', display=None):
        result = subprocess.run(['xclip', '-display', display or self.uu, '-selection', 'clipboard',
                                 '-out', '-target', target], env=self.environment,
                                capture_output=True, timeout=2)
        return result.stdout if result.returncode == 0 else None

    def copy_x(self, display, value):
        subprocess.run(['xclip', '-display', display, '-selection', 'clipboard', '-in'],
                       input=value, env=self.environment, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def test_native_text_and_mime_aliases_reach_uu(self):
        for mime in ('text/plain', 'text/plain;charset=UTF-8', 'text/plain;charset=utf-8'):
            value = ('native copy ' + mime + ' 中文').encode()
            self.copy_native({mime: value})
            self.wait_for(lambda: self.paste() == value)

    def test_image_and_file_list_keep_their_formats(self):
        png = b'\x89PNG\r\n\x1a\nfixture'
        self.copy_native({'image/png': png})
        self.wait_for(lambda: self.paste('image/png') == png)
        uris = b'file:///tmp/clipboard-fixture.txt\r\n'
        self.copy_native({'text/uri-list': uris})
        self.wait_for(lambda: self.paste('text/uri-list') == uris)
        self.assertEqual(self.paste('x-special/gnome-copied-files'),
                         b'copy\nfile:///tmp/clipboard-fixture.txt')

    def test_large_native_transfer_does_not_block(self):
        value = b'large native clipboard ' * 100000
        self.copy_native({'text/plain': value})
        self.wait_for(lambda: self.paste() == value)

    def test_transient_clipboard_is_not_forwarded(self):
        self.copy_native({'text/plain': b'keep clipboard'})
        self.wait_for(lambda: self.paste() == b'keep clipboard')
        self.copy_native({'text/plain': b'typed transient', 'application/x-uurb-transient': b'1'})
        self.wait_for(lambda: b'transient on desktop' in self.read_log())
        self.assertEqual(self.paste(), b'keep clipboard')

    def test_bridge_marker_keeps_phone_files_lazy(self):
        self.copy_native({'text/plain': b'keep clipboard'})
        self.wait_for(lambda: self.paste() == b'keep clipboard')
        self.copy_native({'text/uri-list': b'file:///tmp/not-downloaded-yet\r\n',
                          'application/x-uurb-clipboard-bridge': b''}, delay=1000)
        time.sleep(.2)
        self.assertEqual(self.paste(), b'keep clipboard')
        self.assertIsNone(self.paste('text/uri-list'))

    def test_requests_are_served_during_a_slow_native_copy(self):
        self.copy_native({'text/plain': b'existing copy'})
        self.wait_for(lambda: self.paste() == b'existing copy')
        self.copy_native({'text/plain': b'slow copy'}, delay=1000)
        time.sleep(.1)
        started = time.monotonic()
        self.assertEqual(self.paste(), b'existing copy')
        self.assertLess(time.monotonic() - started, .5)
        self.wait_for(lambda: self.paste() == b'slow copy')

    def test_new_native_copy_supersedes_a_slow_transfer(self):
        self.copy_native({'text/plain': b'old slow copy'}, delay=1000)
        time.sleep(.1)
        self.copy_native({'text/plain': b'new copy'})
        self.wait_for(lambda: self.paste() == b'new copy')
        time.sleep(1.1)
        self.assertEqual(self.paste(), b'new copy')

    def test_both_directions_avoid_echoes(self):
        self.copy_native({'text/plain': b'native text'})
        self.wait_for(lambda: self.paste() == b'native text')
        self.copy_x(self.uu, b'native text')
        self.wait_for(lambda: b'unchanged uu->desktop' in self.read_log())
        self.copy_x(self.uu, b'controller text')
        self.wait_for(lambda: self.paste(display=self.desktop) == b'controller text')
        self.copy_native({'text/plain': b'controller text'})
        self.wait_for(lambda: b'unchanged desktop->uu' in self.read_log())


if __name__ == '__main__':
    unittest.main()
