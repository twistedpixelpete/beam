"""Exported files get normal permissions, keep existing ones, and never end up half written."""
import importlib.util
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'projection_study' / 'export_files.py'
spec = importlib.util.spec_from_file_location('export_files', SOURCE)
export_files = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export_files)


def mode(path):
    return stat.S_IMODE(path.stat().st_mode)


class WriteAtomicTests(unittest.TestCase):
    def setUp(self):
        self.old_mask = os.umask(0o022)
        self.addCleanup(os.umask, self.old_mask)
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        self.path = self.folder / 'out.json'

    def test_new_file_uses_normal_permissions(self):
        export_files.write_atomic(self.path, b'new')
        self.assertEqual(self.path.read_bytes(), b'new')
        self.assertEqual(mode(self.path), 0o644)

    def test_overwriting_keeps_permissions(self):
        self.path.write_bytes(b'old')
        os.chmod(self.path, 0o660)
        export_files.write_atomic(self.path, b'new')
        self.assertEqual(self.path.read_bytes(), b'new')
        self.assertEqual(mode(self.path), 0o660)

    def test_failure_keeps_the_old_file_and_leaves_nothing_behind(self):
        self.path.write_bytes(b'old')
        with patch.object(export_files.os, 'replace', side_effect=OSError('full')):
            with self.assertRaises(OSError):
                export_files.write_atomic(self.path, b'new')
        self.assertEqual(self.path.read_bytes(), b'old')
        self.assertEqual([item.name for item in self.folder.iterdir()], ['out.json'])

    def test_new_folder_mode_follows_umask(self):
        self.assertEqual(export_files.new_folder_mode(), 0o755)


if __name__ == '__main__':
    unittest.main()
