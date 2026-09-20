#!/usr/bin/env python3
"""Validate the exact staged website without changing files or the Git index."""
import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True).stdout


def relevant(name):
    return name in ('index.html', 'site.json', 'exporter.lock.json', 'build-static.sh', 'LICENSE.md', 'THIRD_PARTY_NOTICES.md') or name.startswith(('assets/', 'branding/', 'vendor/logseq-static-garden/', 'tools/', 'licenses/'))


def check(root):
    changed = git(root, 'diff', '--cached', '--name-only', '--diff-filter=ACDMRT', '-z').decode().split('\0')
    if not any(relevant(path) for path in changed):
        return 0
    python = root / '.venv-static/bin/python'
    if not python.is_file():
        print('Static garden: run ./build-static.sh once to set up the local build environment, then retry the commit.', file=sys.stderr)
        return 1
    print('Static garden: validating the staged export (no files will be changed or staged).', flush=True)
    with tempfile.TemporaryDirectory(prefix='garden-staged-') as temporary:
        snapshot = Path(temporary) / 'source'
        snapshot.mkdir()
        # checkout-index reads the index, including partially staged files and deletions.
        # It never substitutes unstaged working-tree versions.
        git(root, 'checkout-index', '--all', '--prefix=' + str(snapshot) + os.sep)
        required = ['index.html', 'build-static.sh', 'vendor/logseq-static-garden/static-garden/build.py',
                    'vendor/logseq-static-garden/static-garden/requirements.txt',
                    'site.json', 'branding/logo.png', 'branding/logo.svg', 'exporter.lock.json', 'tools/exporter.py']
        missing = [path for path in required if not (snapshot / path).is_file()]
        if missing:
            print('Static garden: required files are missing from the staged commit:\n  ' + '\n  '.join(missing), file=sys.stderr)
            print('Stage the complete converter and public export before committing.', file=sys.stderr)
            return 1
        pinned = subprocess.run([sys.executable, str(snapshot / 'tools/exporter.py'), 'verify', '--root', str(snapshot)])
        if pinned.returncode:
            return pinned.returncode
        # Dependency changes must be installed deliberately, never downloaded by a hook.
        verify = '''import importlib.metadata, pathlib, sys
for line in pathlib.Path(sys.argv[1]).read_text().splitlines():
    line = line.strip()
    if not line or line.startswith('#'): continue
    name, expected = line.split('==', 1)
    try: actual = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError: actual = 'not installed'
    if actual != expected:
        sys.exit(f'{name}: need {expected}, found {actual}. Run ./build-static.sh before committing.')
'''
        deps = subprocess.run([str(python), '-c', verify, str(snapshot / 'vendor/logseq-static-garden/static-garden/requirements.txt')])
        if deps.returncode:
            return deps.returncode
        result = subprocess.run([str(python), str(snapshot / 'vendor/logseq-static-garden/static-garden/build.py'),
                                 '--source', str(snapshot), '--output', str(Path(temporary) / 'dist')], cwd=snapshot)
        if result.returncode:
            print('Static garden: the staged version does not build. Fix and stage the changes, then retry.', file=sys.stderr)
        return result.returncode


if __name__ == '__main__':
    try:
        sys.exit(check(Path(sys.argv[1]).resolve()))
    except (OSError, subprocess.CalledProcessError) as error:
        print(f'Static garden pre-commit failed: {error}', file=sys.stderr)
        sys.exit(1)
