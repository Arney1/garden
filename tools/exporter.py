#!/usr/bin/env python3
"""Check or update the exact exporter snapshot used by this personal site."""
import argparse
from hashlib import sha256
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parent.parent
VENDOR = 'vendor/logseq-static-garden'
LOCK = 'exporter.lock.json'


def manifest(root):
    result = {}
    for path in sorted(root.rglob('*')):
        # Python may create caches while running the exporter.
        if '__pycache__' in path.parts:
            continue
        if path.is_symlink():
            raise ValueError(f'Unexpected symlink in exporter: {path}')
        if path.is_file():
            result[path.relative_to(root).as_posix()] = sha256(path.read_bytes()).hexdigest()
    return result


def verify(root):
    lock = json.loads((root / LOCK).read_text())
    actual = manifest(root / VENDOR)
    if not actual or actual != lock['files']:
        raise ValueError('Exporter snapshot differs from exporter.lock.json. Update it with tools/exporter.py; make renderer edits in logseq-static-garden.')
    return lock


def git(checkout, *args):
    return subprocess.run(['git', '-C', str(checkout), *args], check=True, capture_output=True).stdout


def update(root, checkout, revision):
    destination = root / VENDOR
    if destination.exists():
        verify(root)  # Never overwrite local edits to the pinned copy.
    if git(checkout, 'status', '--porcelain').strip():
        raise ValueError('Exporter checkout has uncommitted changes. Test and commit them before updating the pin.')
    commit = git(checkout, 'rev-parse', '--verify', revision + '^{commit}').decode().strip()
    archive = git(checkout, 'archive', '--format=tar', commit)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.exporter-update-', dir=destination.parent) as temporary:
        temporary = Path(temporary)
        staged = temporary / 'new'
        staged.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            for member in tar.getmembers():
                name = PurePosixPath(member.name)
                if name.is_absolute() or '..' in name.parts or '.git' in name.parts or not (member.isfile() or member.isdir()):
                    raise ValueError(f'Unsupported archive entry: {member.name}')
                target = staged / name
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(tar.extractfile(member).read())
                    target.chmod(0o755 if member.mode & 0o111 else 0o644)
        for name in ('static-garden/build.py', 'static-garden/requirements.txt', 'vendor/katex/katex.min.js', 'LICENSE.md', 'AUTHORS.md'):
            if not (staged / name).is_file():
                raise ValueError(f'Not a complete exporter checkout: missing {name}')
        lock = {'project': 'logseq-static-garden', 'commit': commit, 'files': manifest(staged)}
        backup = temporary / 'previous'
        had_old = destination.exists()
        if had_old:
            destination.rename(backup)
        try:
            staged.rename(destination)
            new_lock = temporary / 'lock.json'
            new_lock.write_text(json.dumps(lock, indent=2, sort_keys=True) + '\n')
            new_lock.replace(root / LOCK)
        except BaseException:
            if destination.exists():
                shutil.rmtree(destination)
            if had_old:
                backup.rename(destination)
            raise
    print(f'Pinned logseq-static-garden at {commit}. Review, build, and commit the vendor directory and lock together.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    check = sub.add_parser('verify')
    check.add_argument('--root', type=Path, default=ROOT)
    install = sub.add_parser('update')
    install.add_argument('checkout', type=Path)
    install.add_argument('--revision', default='HEAD')
    args = parser.parse_args()
    try:
        if args.action == 'verify':
            verify(args.root)
        else:
            update(ROOT, args.checkout.resolve(), args.revision)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Exporter: {error}\n')


if __name__ == '__main__':
    main()
