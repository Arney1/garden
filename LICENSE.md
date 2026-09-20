# Licensing

This repository contains separately licensed software and garden content.

## Static exporter: MIT

Copyright (c) 2026 Arney Nova. The following original project files are licensed
under the [MIT License](licenses/MIT.txt):

- Original site build and validation scripts in `tools/`, including tests.
- The exporter snapshot in `vendor/logseq-static-garden/` retains its own MIT license, dependency notices, and contributor credits.
- `build-static.sh`, `install-hooks.sh`, and `.githooks/pre-commit`.
- The root README and deployment documentation, excluding quoted third-party material.
- The HTML layout and original browser code emitted by the exporter.

Third-party code or notices included in these files keep their own terms.
The MIT grant covers the software, not the notes rendered through it.

## Logseq and other third-party components

Logseq's original export runtime is covered by the
[GNU Affero General Public License, version 3](licenses/Logseq-AGPL-3.0.txt),
with bundled dependencies retaining their respective licenses. It is not
relicensed under MIT. See [third-party notices and source links](THIRD_PARTY_NOTICES.md)
and [the export's source reference](static/SOURCES.md).

## Notes, attachments, and identity

The software license does not grant permission to reuse garden text, exported
graph data, attachments in `assets/`, screenshots, `site.json`,
or the site's name and logo (including `branding/`). Original
content remains copyright its author, with all rights reserved unless stated
otherwise. Third-party material remains subject to its owner's terms. Existing
licenses, permissions, and rights provided by law are unaffected.

Logseq is the name of the upstream project. This exporter is an independent,
unofficial project and does not imply endorsement by Logseq.
