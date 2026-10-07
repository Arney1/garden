# Third-party notices

This exporter reads Logseq's public export format. The Logseq application runtime
is not included in this repository or in generated sites. Publishers who retain
or redistribute their original exports must keep those exports' upstream notices.

## Components used by the static build

| Component | Role | License text |
| --- | --- | --- |
| markdown-it-py 4.2.0 and upstream markdown-it | Markdown parser | [MIT](licenses/markdown-it-py/LICENSE.txt), [upstream notice](licenses/markdown-it-py/LICENSE.markdown-it.txt) |
| mdit-py-plugins 0.6.1 | Markdown extensions | [MIT](licenses/mdit-py-plugins/LICENSE.txt); additional plugin notices are retained in that directory |
| mdurl 0.1.2 | URL parsing dependency | [MIT](licenses/mdurl/LICENSE.txt) |
| Pygments 2.21.0 | Highlighted code and generated stylesheet rules | [BSD-2-Clause](licenses/pygments/LICENSE.txt), [authors](licenses/pygments/AUTHORS.txt) |
| KaTeX 0.16.45 | Build-time MathML rendering | [MIT](licenses/katex/LICENSE.txt) |
| Mermaid 10.9.3 | Client-side diagram rendering on pages that use diagrams | [MIT](licenses/mermaid/LICENSE.txt) |

The generated site includes the exporter's original browser code, rendered
content, and Pygments stylesheet output. It does not ship KaTeX, Python packages,
or the original Logseq runtime. License texts are published under `/licenses/`.


## Bundled KaTeX

`vendor/katex/katex.min.js` is KaTeX 0.16.45, copied unchanged from the original
Logseq export. Its MIT notice is in `licenses/katex/LICENSE.txt`.
Source: https://github.com/KaTeX/KaTeX/tree/v0.16.45

KaTeX executes at build time; visitors receive MathML, not the KaTeX bundle.
The source export's JavaScript is never executed by the build.

## Bundled Mermaid

`vendor/mermaid/mermaid.min.js` is Mermaid 10.9.3 (the last release that ships
a self-contained classic-script bundle), downloaded from the npm registry and
stored unchanged. Its MIT notice and checksums are recorded in
`licenses/sources.json`. Source: https://github.com/mermaid-js/mermaid/tree/v10.9.3

Unlike KaTeX, Mermaid needs a real browser layout engine, so diagrams render
in the visitor's browser instead of at build time. The bundle is copied into
the generated site **only when a page contains a diagram**, and pages without
diagrams never download it. Diagram sources stay readable without JavaScript;
Mermaid runs with `securityLevel: 'strict'` and the site's `script-src 'self'`
policy still applies.

`licenses/sources.json` records the provenance and checksums of retained notices.
