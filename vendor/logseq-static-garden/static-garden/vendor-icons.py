#!/usr/bin/env python3
"""Refresh trusted build-time icon data. Normal builds never use the network."""
import base64
import gzip
from hashlib import sha512
import io
import json
from pathlib import Path
import tarfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
PACKAGES = [
    ('tabler', 'https://registry.npmjs.org/@tabler/icons/-/icons-3.50.0.tgz',
     'HflLxyrH1cqC7s7jzQGSjpsTAVIoaf7+/yHjbdM59rJQBMjliibp+LYhDPFxOMcwa1M8DNpOk6ENzQiWn9a1Dg=='),
    ('emoji-mart', 'https://registry.npmjs.org/@emoji-mart/data/-/data-1.2.1.tgz',
     'no2pQMWiBy6gpBEiqGeU77/bFejDqUTRY7KX+0+iur13op3bqUsXdnwoZs6Xb1zbv0gAj5VvS1PWoUUckSr5Dw=='),
]


def main():
    target = ROOT / 'vendor/icons'
    target.mkdir(parents=True, exist_ok=True)
    provenance = []
    for name, url, integrity in PACKAGES:
        archive = urlopen(url).read()
        if sha512(archive).digest() != base64.b64decode(integrity):
            raise ValueError(f'Integrity mismatch: {name}')
        with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
            license_text = tar.extractfile('package/LICENSE').read()
            notice = ROOT / f'licenses/{name}/LICENSE.txt'
            notice.parent.mkdir(parents=True, exist_ok=True)
            notice.write_bytes(license_text)
            if name == 'tabler':
                data = {}
                for member in tar.getmembers():
                    parts = Path(member.name).parts
                    if len(parts) == 4 and parts[:2] == ('package', 'icons') and member.name.endswith('.svg'):
                        # The Logseq picker uses PascalCase plus a Filled suffix.
                        key = ''.join(word.capitalize() for word in Path(member.name).stem.split('-'))
                        if parts[2] == 'filled':
                            key += 'Filled'
                        data[key.casefold()] = tar.extractfile(member).read().decode()
            else:
                emojis = json.load(tar.extractfile('package/sets/15/native.json'))['emojis']
                data = {key: [skin['native'] for skin in value['skins']] for key, value in emojis.items()}
                for key, value in emojis.items():
                    for alias in value.get('aliases', []):
                        data[alias] = data[key]
            packed = gzip.compress(json.dumps(data, ensure_ascii=False, sort_keys=True,
                                              separators=(',', ':')).encode(), mtime=0)
            (target / f'{name}.json.gz').write_bytes(packed)
            provenance.append({'name': name, 'source': url, 'integrity': 'sha512-' + integrity})
    (target / 'sources.json').write_text(json.dumps(provenance, indent=2) + '\n')


if __name__ == '__main__':
    main()
