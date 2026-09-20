# Third-party notices

The reusable exporter is maintained separately and pinned under
`vendor/logseq-static-garden/`; its own notices and contributor credits travel
with that snapshot. The garden exporter is independently implemented. Logseq provides the source
export format and inspired the outline interface. This repository also retains
the original export runtime and its dependencies; the MIT license for the new
exporter does not replace their licenses.

## Logseq source

The checked-in `static/js/main.js` identifies itself as **2.0.1**, Git revision
**`b09316abd7bde39d25c6c5694d01b2d4e874fe01`** (short revision `b09316a`). The source reference
uses that embedded revision, rather than assuming the `2.0.1` release tag matches.

- [Source tree](https://github.com/logseq/logseq/tree/b09316abd7bde39d25c6c5694d01b2d4e874fe01)
- [Download source archive](https://github.com/logseq/logseq/archive/b09316abd7bde39d25c6c5694d01b2d4e874fe01.tar.gz)
- [Build and contributor instructions](https://github.com/logseq/logseq/blob/b09316abd7bde39d25c6c5694d01b2d4e874fe01/CONTRIBUTING.md)
- [JavaScript dependency lockfile](https://github.com/logseq/logseq/blob/b09316abd7bde39d25c6c5694d01b2d4e874fe01/pnpm-lock.yaml)
- [Clojure dependencies](https://github.com/logseq/logseq/blob/b09316abd7bde39d25c6c5694d01b2d4e874fe01/deps.edn)
- [AGPLv3 license](licenses/Logseq-AGPL-3.0.txt)

The public export's original JavaScript, CSS, workers, and WASM remain under
`static/`. The static exporter does not rebuild or modify those runtime bundles.
Garden-specific export HTML, custom CSS/JS, and the replaced logo are distinct
from the upstream runtime; local project changes are recorded in this repository's
history. Exported graph text is content, not Logseq program code.

The source archive includes upstream build scripts and dependency declarations.
Retain these source directions beside redistributed runtime bundles. When a new
export changes its embedded Git revision, update this reference and review the
bundled component versions and notices. A version label alone is not a source
match, and a separately modified runtime also needs its modified source provided.

## Components used by the static build

| Component | Role | License text |
| --- | --- | --- |
| markdown-it-py 4.2.0 and upstream markdown-it | Markdown parser | [MIT](licenses/markdown-it-py/LICENSE.txt), [upstream notice](licenses/markdown-it-py/LICENSE.markdown-it.txt) |
| mdit-py-plugins 0.6.1 | Markdown extensions | [MIT](licenses/mdit-py-plugins/LICENSE.txt); additional plugin notices are retained in that directory |
| mdurl 0.1.2 | URL parsing dependency | [MIT](licenses/mdurl/LICENSE.txt) |
| Pygments 2.21.0 | Highlighted code and generated stylesheet rules | [BSD-2-Clause](licenses/pygments/LICENSE.txt), [authors](licenses/pygments/AUTHORS.txt) |
| KaTeX 0.16.45 | Build-time MathML rendering from the pinned exporter bundle; also present in the raw export | [MIT](licenses/katex/LICENSE.txt) |

The generated site includes the exporter's original browser code, rendered
content, and Pygments stylesheet output. It does not ship KaTeX, Python packages,
or the original Logseq runtime. License texts are published under `/licenses/`.

## Components retained in the raw export

These notices supplement copyright and license comments already present in
`static/` and the adjacent `*.LICENSE.txt` files. Preserve both. Version numbers
below come from bundle headers or the matching upstream dependency declarations;
files without a reliable version are identified by their upstream project.

| Component | License text |
| --- | --- |
| React / React DOM 19.2.6 | [React MIT](licenses/react/LICENSE.txt), [React DOM MIT](licenses/react-dom/LICENSE.txt) |
| Tabler React icons 3.44.0 / icon webfont 2.47.0 | [React icons MIT](licenses/tabler--icons-react/LICENSE.txt), [webfont MIT](licenses/Tabler-2.47.0.txt) |
| Inter 4.1 font files | [SIL Open Font License 1.1](licenses/inter-ui/LICENSE.txt) |
| KaTeX font files | [MIT](licenses/KaTeX-FONTS.txt) |
| Highlight.js 11.11.1 | [BSD-3-Clause](licenses/highlightjs--cdn-assets/LICENSE.txt) |
| html2canvas 1.4.1 | [MIT](licenses/html2canvas/LICENSE.txt) |
| interact.js 1.10.27 | [MIT](licenses/interactjs/LICENSE.txt) |
| Marked 17.0.6 | [MIT](licenses/marked/LICENSE.md.txt) |
| DOMPurify 3.4.2; 3.3.3 in plugin bundles | [Apache-2.0 OR MPL-2.0](licenses/dompurify/LICENSE.txt), [3.3.3 text](licenses/DOMPurify-3.3.3.txt) |
| PhotoSwipe 5.4.4 | [MIT](licenses/photoswipe/LICENSE.txt) |
| Glide 3.7.1 | [MIT](licenses/glidejs--glide/LICENSE.txt) |
| LightningFS 4.6.2 | [MIT](licenses/isomorphic-git--lightning-fs/LICENSE.txt) |
| EventEmitter3 / MagicPortal / prop-types | [MIT](licenses/eventemitter3/LICENSE.txt), [MIT](licenses/magic-portal/LICENSE.txt), [MIT](licenses/prop-types/LICENSE.txt) |
| PDF.js and its font/CMap resources | [Apache-2.0](licenses/pdfjs-dist/LICENSE.txt), [CMaps](licenses/pdfjs-dist/cmaps--LICENSE.txt), [Foxit](licenses/pdfjs-dist/standard_fonts--LICENSE_FOXIT.txt), [Liberation](licenses/pdfjs-dist/standard_fonts--LICENSE_LIBERATION.txt) |
| Google Closure Library | [Apache-2.0](licenses/Closure.txt) |
| ClojureScript | [Eclipse Public License 1.0](licenses/ClojureScript.txt) |
| SQLite WASM / Emscripten glue | SQLite public-domain notice remains in `static/js/db-worker-bundle.js.LICENSE.txt`; [Emscripten MIT/NCSA notices](licenses/Emscripten.txt) |

The original bundles contain additional transitive dependencies. Their supplied
notices and the upstream source/dependency files remain authoritative; this table
is a guide to the separately distributed components, not a replacement license
for the entire Logseq dependency tree.

## License provenance

[licenses/sources.json](licenses/sources.json) records where each added upstream
license text was obtained and its SHA-256 checksum. `license_source_version`
identifies the package from which a notice was retrieved; it does not claim that
an otherwise unversioned bundle was built from that exact package. No dependency
code was changed or installed to collect these notices.

## Content and branding

Notes, screenshots, linked resources, attachments, and the site's identity are
outside the exporter software license. Their presence in a public export does
not grant a new redistribution license. See [LICENSE.md](LICENSE.md) for scope.
