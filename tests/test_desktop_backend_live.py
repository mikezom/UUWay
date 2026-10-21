"""Real Plasma/AT-SPI regression. Opt in with UUWAY_LIVE_DESKTOP_TESTS=1.

Only reads topology and connection metadata; never changes accessibility policy,
reads field contents, locks the desktop, or restarts services.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import unittest

from tests.test_desktop_backend import backend

Gio = GLib = None
if os.environ.get('UUWAY_LIVE_DESKTOP_TESTS') == '1':
    try:
        import gi
        from gi.repository import Gio, GLib
    except ImportError:
        pass

ROOT = Path(__file__).resolve().parents[1]
QUERY = '''import json,subprocess,sys
sys.path.insert(0,sys.argv[1])
import desktop_backend
if sys.argv[2]=='control':
    result=subprocess.run(['kscreen-doctor','-j'],capture_output=True,text=True,check=True,timeout=5)
    topology=desktop_backend.plasma_topology(json.loads(result.stdout))
else:
    topology=desktop_backend.current_plasma_topology()
print(json.dumps(topology))
'''


@unittest.skipUnless(Gio is not None, 'Requires UUWAY_LIVE_DESKTOP_TESTS=1, Plasma Wayland, and PyGObject')
class PlasmaAccessibilityTests(unittest.TestCase):
    def test_topology_queries_do_not_connect_to_accessibility_bus(self):
        if not backend.plasma_wayland() or not shutil.which('kscreen-doctor'):
            self.skipTest('A live Plasma Wayland session with kscreen-doctor is required')
        session = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        status = session.call_sync('org.a11y.Bus', '/org/a11y/bus',
            'org.freedesktop.DBus.Properties', 'GetAll', GLib.Variant('(s)', ('org.a11y.Status',)),
            GLib.VariantType.new('(a{sv})'), Gio.DBusCallFlags.NO_AUTO_START, 1000, None).unpack()[0]
        if status.get('IsEnabled') or status.get('ScreenReaderEnabled'):
            self.skipTest('Desktop accessibility is enabled; do not override its policy for a test')
        address = session.call_sync('org.a11y.Bus', '/org/a11y/bus', 'org.a11y.Bus', 'GetAddress',
            None, GLib.VariantType.new('(s)'), Gio.DBusCallFlags.NO_AUTO_START, 1000, None).unpack()[0]
        connection = Gio.DBusConnection.new_for_address_sync(address,
            Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION,
            None, None)
        self.addCleanup(connection.close_sync, None)
        loop = GLib.MainLoop()
        processes, children, observations, results, errors = {}, [], [], [], []

        def changed(bus, sender, path, interface, signal, parameters, data):
            name, previous, current = parameters.unpack()
            if not current or not name.startswith(':'):
                return
            try:
                pid = bus.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus',
                    'org.freedesktop.DBus', 'GetConnectionUnixProcessID', GLib.Variant('(s)', (current,)),
                    GLib.VariantType.new('(u)'), Gio.DBusCallFlags.NONE, 300, None).unpack()[0]
                process_status = (Path('/proc') / str(pid) / 'status').read_text()
                parent = int(next(line.split()[1] for line in process_status.splitlines()
                                  if line.startswith('PPid:')))
                if parent in processes:
                    observations.append(processes[parent])
            except (GLib.Error, FileNotFoundError, ProcessLookupError):
                # Other desktop clients can disconnect before their metadata is read.
                pass

        subscription = connection.signal_subscribe('org.freedesktop.DBus', 'org.freedesktop.DBus',
            'NameOwnerChanged', '/org/freedesktop/DBus', None, Gio.DBusSignalFlags.NONE, changed, None)
        self.addCleanup(connection.signal_unsubscribe, subscription)

        def run_queries():
            try:
                # The positive control proves that the live observer can see Qt registration.
                environment = dict(os.environ, QT_LINUX_ACCESSIBILITY_ALWAYS_ON='1',
                                   AT_SPI_BUS_ADDRESS=address)
                for label in ('control', 'query', 'query', 'query'):
                    process = subprocess.Popen([sys.executable, '-c', QUERY, str(ROOT / 'scripts'), label],
                        env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    processes[process.pid] = label
                    children.append(process)
                    try:
                        output, stderr = process.communicate(timeout=8)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.communicate()
                        raise
                    if process.returncode:
                        raise RuntimeError('Topology query failed: ' + stderr[-2000:])
                    results.append(json.loads(output))
            except Exception as error:
                errors.append(error)
            finally:
                GLib.idle_add(loop.quit)

        worker = threading.Thread(target=run_queries, daemon=True)
        worker.start()
        # Each query is bounded; this deadline also covers a broken observer.
        expired = []

        def deadline():
            expired.append(True)
            loop.quit()
            return False

        timeout = GLib.timeout_add_seconds(35, deadline)
        try:
            loop.run()
        finally:
            if worker.is_alive():
                for process in children:
                    if process.poll() is None:
                        process.terminate()
            worker.join(timeout=2)
            if not expired:
                GLib.source_remove(timeout)
        self.assertFalse(worker.is_alive(), 'Topology test exceeded its deadline')
        if errors:
            raise errors[0]
        self.assertEqual(len(results), 4)
        self.assertIn('control', observations, 'Positive control did not register; observation is inconclusive')
        self.assertNotIn('query', observations, 'Topology polling registered an unnecessary AT-SPI client')
        self.assertTrue(all(value == results[0] for value in results), 'Topology changed during verification')


if __name__ == '__main__':
    unittest.main()
