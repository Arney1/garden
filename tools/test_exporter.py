"""Pinned snapshots are self-contained and accidental local changes are rejected."""
from pathlib import Path
import json
import subprocess
import tempfile
import unittest

from exporter import manifest, update, verify


class SnapshotTests(unittest.TestCase):
    def test_update_from_commit_is_reproducible_and_detects_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout = root / 'engine'
            checkout.mkdir()
            site = root / 'site'
            site.mkdir()
            for name in ('static-garden/build.py', 'static-garden/requirements.txt', 'vendor/katex/katex.min.js', 'LICENSE.md', 'AUTHORS.md'):
                file = checkout / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text('fixture')
            def git(*args):
                return subprocess.run(['git', '-C', str(checkout), *args], check=True, capture_output=True)
            git('init', '-q'); git('add', '.')
            git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'Fixture')
            update(site, checkout, 'HEAD')
            lock = verify(site)
            self.assertEqual(lock['commit'], git('rev-parse', 'HEAD').stdout.decode().strip())
            self.assertFalse((site / 'vendor/logseq-static-garden/.git').exists())
            file = site / 'vendor/logseq-static-garden/static-garden/build.py'
            file.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'snapshot differs'):
                verify(site)
            with self.assertRaisesRegex(ValueError, 'snapshot differs'):
                update(site, checkout, 'HEAD')
            self.assertEqual(file.read_text(), 'changed')

    def test_extra_files_and_symlinks_are_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vendor = root / 'vendor/logseq-static-garden'
            vendor.mkdir(parents=True)
            (vendor / 'file').write_text('original')
            (root / 'exporter.lock.json').write_text(json.dumps({'files': manifest(vendor)}))
            (vendor / 'extra').write_text('unexpected')
            with self.assertRaises(ValueError): verify(root)
            (vendor / 'extra').unlink()
            (vendor / 'link').symlink_to('/etc/passwd')
            with self.assertRaisesRegex(ValueError, 'symlink'): verify(root)
