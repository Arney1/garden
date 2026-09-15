"""Exercise pre-commit against real isolated Git indices, including partial staging."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


class HookTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git('init', '-q')
        for path, content in {
            'index.html': 'valid staged export', 'build-static.sh': '#!/bin/sh\n',
            'static-garden/requirements.txt': '', 'static-garden/branding/logo.png': 'logo',
            'static-garden/branding/logo.svg': 'logo', 'static/js/katex.min.js': 'renderer',
            'assets/example.txt': 'original', 'README.md': 'read me',
        }.items():
            self.write(path, content)
        self.write('static-garden/build.py', '''from pathlib import Path
import sys
root=Path(sys.argv[sys.argv.index('--source')+1])
assert root.joinpath('index.html').read_text() == 'valid staged export', 'Staged export failed'
assert root.joinpath('assets/example.txt').read_text() == 'original', 'Unstaged asset was used'
assert not root.joinpath('assets/untracked.txt').exists(), 'Untracked asset was included'
''')
        self.git('add', '.')
        # Local identity applies only to this throwaway fixture.
        self.git('-c', 'user.name=Hook Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'Initial fixture')
        (self.root / '.venv-static/bin').mkdir(parents=True)
        (self.root / '.venv-static/bin/python').symlink_to(sys.executable)

    def write(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], capture_output=True, check=True).stdout

    def run_hook(self):
        before = self.git('diff', '--cached', '--binary')
        result = subprocess.run([sys.executable, str(HERE / 'check-staged.py'), str(self.root)], text=True, capture_output=True)
        self.assertEqual(before, self.git('diff', '--cached', '--binary'), 'Hook modified staging')
        return result

    def test_docs_commit_ignores_unstaged_broken_export(self):
        self.write('README.md', 'changed'); self.git('add', 'README.md')
        self.write('index.html', 'broken unstaged export')
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertEqual((self.root/'index.html').read_text(), 'broken unstaged export')

    def test_partial_staging_uses_staged_export_and_assets(self):
        self.write('static-garden/requirements.txt', '# update\n'); self.git('add', 'static-garden/requirements.txt')
        self.write('index.html', 'broken unstaged export')
        self.write('assets/example.txt', 'unstaged change')
        self.write('assets/untracked.txt', 'do not commit')
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root/'assets/example.txt').read_text(), 'unstaged change')
        self.assertNotIn(b'assets/untracked.txt', self.git('ls-files'))

    def test_staged_broken_export_is_rejected_even_if_worktree_fixed(self):
        self.write('index.html', 'broken'); self.git('add', 'index.html')
        self.write('index.html', 'valid staged export')
        result = self.run_hook()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('staged version does not build', result.stderr)

    def test_staged_deletion_is_checked(self):
        self.git('rm', '--cached', 'static/js/katex.min.js')
        result = self.run_hook()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('static/js/katex.min.js', result.stderr)
        self.assertTrue((self.root/'static/js/katex.min.js').exists())

    def test_missing_dependencies_do_not_trigger_install(self):
        self.write('static-garden/requirements.txt', 'this-package-does-not-exist==1.0\n'); self.git('add', 'static-garden/requirements.txt')
        result = self.run_hook()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Run ./build-static.sh', result.stderr)

    def test_hook_install_preserves_original_and_is_idempotent(self):
        installer = HERE.parent / 'install-hooks.sh'
        shutil.copy2(installer, self.root/'install-hooks.sh')
        hook = self.root/'.git/hooks/pre-commit'
        original = '#!/bin/sh\necho old-compression-hook\n'
        hook.write_text(original)
        for _ in range(2):
            result = subprocess.run(['bash', str(self.root/'install-hooks.sh')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(hook.with_name('pre-commit.before-static-garden').read_text(), original)
        self.assertIn('garden hook dispatcher', hook.read_text())


if __name__ == '__main__':
    unittest.main()
