# Logseq export: license and source

The runtime in this directory reports Logseq **2.0.1**, Git revision
**`b09316abd7bde39d25c6c5694d01b2d4e874fe01`**, in `js/main.js`.

It retains [AGPLv3](../licenses/Logseq-AGPL-3.0.txt) terms. Bundled dependencies
retain their own licenses and copyright notices, including the adjacent
`*.LICENSE.txt` files.

Corresponding upstream source, including build scripts and dependency manifests:

- [Browse source](https://github.com/logseq/logseq/tree/b09316abd7bde39d25c6c5694d01b2d4e874fe01)
- [Download source](https://github.com/logseq/logseq/archive/b09316abd7bde39d25c6c5694d01b2d4e874fe01.tar.gz)
- [Third-party notices](../THIRD_PARTY_NOTICES.md)

The new static exporter lives in `../static-garden/`; it does not modify these
runtime bundles. Garden customizations to export HTML, custom styles/scripts,
and the logo are recorded in this repository. New runtime exports require a
matching source reference; modified runtime bundles require their modified source.
