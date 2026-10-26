import importlib.util
import os
from pathlib import Path
import socket
import subprocess
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
try:
    spec = importlib.util.spec_from_file_location('native_text_service', ROOT / 'scripts/uu-native-text-service.py')
    service = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(service)
finally:
    sys.path.pop(0)


class TextServiceTests(unittest.TestCase):
    def test_system_python_daemon_is_adopted_independently_of_minor_version(self):
        with tempfile.TemporaryDirectory() as name:
            endpoint = Path(name) / 'text.sock'
            restore = Path(name) / 'restore.json'
            script = Path(name) / 'text.py'
            script.write_text('''import os, socket, sys, time
s = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
s.bind(sys.argv[2]); os.chmod(sys.argv[2], 0o600); s.listen(1)
print('ready', flush=True)
time.sleep(30)
''')
            child = subprocess.Popen(['/usr/bin/python3', str(script), '--socket', str(endpoint),
                                      '--restore-state', str(restore)], stdout=subprocess.PIPE, text=True)
            try:
                self.assertEqual(child.stdout.readline().strip(), 'ready')
                with patch.object(service, 'DAEMON', script):
                    pid, pidfd = service.live_daemon(endpoint, restore)
                    try:
                        self.assertEqual(pid, child.pid)
                    finally:
                        os.close(pidfd)
                    with patch.object(service.os.path, 'samefile', return_value=False):
                        with self.assertRaisesRegex(ValueError, 'executable'):
                            service.live_daemon(endpoint, restore)
            finally:
                child.terminate(); child.wait(timeout=5); child.stdout.close()

    def test_stale_owned_socket_is_reclaimed_not_timed_out_live_process(self):
        with tempfile.TemporaryDirectory() as name:
            endpoint = Path(name) / 'text.sock'
            with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as old:
                old.bind(str(endpoint)); endpoint.chmod(0o600)
            self.assertIsNone(service.live_daemon(endpoint, Path(name) / 'restore.json'))
            self.assertFalse(endpoint.exists())

    def test_child_between_bind_and_listen_keeps_its_socket(self):
        with tempfile.TemporaryDirectory() as name:
            endpoint = Path(name) / 'text.sock'
            with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as child:
                child.bind(str(endpoint)); endpoint.chmod(0o600)
                self.assertIsNone(service.live_daemon(endpoint, Path(name) / 'restore.json', reclaim_stale=False))
                self.assertTrue(endpoint.exists())

    def test_unrelated_live_listener_is_neither_adopted_nor_removed(self):
        with tempfile.TemporaryDirectory() as name:
            endpoint = Path(name) / 'text.sock'
            with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as other:
                other.bind(str(endpoint)); endpoint.chmod(0o600); other.listen(1)
                with self.assertRaises(ValueError):
                    service.live_daemon(endpoint, Path(name) / 'restore.json')
                self.assertTrue(endpoint.exists())

    def test_non_socket_is_preserved(self):
        with tempfile.TemporaryDirectory() as name:
            endpoint = Path(name) / 'text.sock'; endpoint.touch(mode=0o600)
            with self.assertRaises(ValueError):
                service.live_daemon(endpoint, Path(name) / 'restore.json')
            self.assertTrue(endpoint.is_file())


if __name__ == '__main__':
    unittest.main()
