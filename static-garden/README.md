# Static garden exporter

Converts **Logseq 2.0.1 DB-graph → Export public pages** into ordinary HTML pages.
The original `index.html`, patches, and Logseq checkout stay intact. `dist/` is the
website to deploy. Do not deploy the raw export directory for this version.

## Build and preview

From the garden repository:

```sh
./build-static.sh
python3 -m http.server 8000 --directory dist
```

Open http://localhost:8000. Use HTTP, not `file://`, because links are root-relative.
The build requires Python 3.10+ with venv support and Node.js. Python dependencies
are pinned in `requirements.txt`; Node only runs the KaTeX file already present in
the Logseq export. No npm install is required to build or use the website.

The wrapper creates `.venv-static/` and installs the pinned Python dependencies.
After initial setup, this also works without an internet connection:

```sh
.venv-static/bin/python static-garden/build.py
```

Optional arguments:

```sh
./build-static.sh --source /path/to/public-pages --output /path/to/static-site
```

The generator replaces only directories marked as its own generated output. It
refuses to replace the source export or an unrelated nonempty directory. It builds
and validates a temporary directory before replacing the previous output.

## Publish to Cloudflare Pages

For a Pages project connected to this Git repository, set:

- Framework preset: **None**
- Build command: **`./build-static.sh`**
- Build output directory: **`dist`**
- Root directory: the garden repository root

Commit the converter, wrapper, and refreshed export when you want the normal Pages
Git deployment to rebuild. For a direct upload, upload the **contents of `dist/`**.
The converter does not deploy, push commits, or change the Cloudflare dashboard.

The generated `_headers` replaces the need for the export's COOP/COEP headers.
Only CSS and JS with content hashes receive immutable caching. HTML and attachments
use Pages defaults. The generated real `404.html` prevents the SPA fallback, and
`sitemap.xml` contains every generated page. Change `url` in `site.json` when you
switch to your portfolio's custom domain.

Cloudflare references:
- https://developers.cloudflare.com/pages/framework-guides/deploy-anything/
- https://developers.cloudflare.com/pages/configuration/serving-pages/
- https://developers.cloudflare.com/pages/configuration/headers/

## After editing your Logseq graph

1. Export public pages into this garden repository as before.
2. Run `./build-static.sh` (or let the Pages build run it).
3. Preview `dist/` and check `dist-report.json` for source-content issues.
4. Deploy `dist/`.

`patch-index.py` is no longer needed for the static build. Running it on the input
still works; the converter reads the embedded data and ignores the injected
scripts. The old `compress-assets.sh` is optional for oversized source attachments.
The converter fails with the filename if a used attachment exceeds Pages' 25 MiB
limit. It never silently drops an oversized attachment.

## What survives

- Page content exists in the HTML response, including nested block order,
  headings, collapse state, code, tables, quotes, and images.
- Page and block references become real links and block anchors. Old
  `#/page/name` and `#/page/UUID` bookmarks redirect with a tiny optional script.
- Tag collections, nested pages, and linked references are calculated at build time.
- Custom properties, status, and links remain visible.
- Code highlighting and equations are pre-rendered. Equations use native MathML;
  visitors do not download KaTeX or font bundles.
- Referenced local assets are copied. Images load lazily except the homepage hero;
  audio/video wait for interaction. PDF references open the actual PDF; annotation
  links preserve their PDF page number.
- Graph view lives at `/graph/`, with pan, zoom, dragging, search, connected-page
  links, and an optional selected-page neighborhood. A note's Graph view link
  opens its local neighborhood. Layout runs in Node at build time; the small
  Canvas viewer and graph JSON load only when visiting the graph.
- All-pages browsing and native block collapsing work with JavaScript disabled.
- Full-text search downloads its JSON index on the first query, not on first load.
- Independent tabs work normally; there are no locks, database workers, browser
  database storage, React, or WASM in the generated website.

## Boundaries

This is a reading website. It does not run Logseq plugins, editing, flashcard
scheduling, arbitrary Hiccup/HTML, or live Datalog queries. Graph view visualizes
the exported public-page relationships; it does not need a browser database.
The current export has one advanced query ("duplicate pages"); its source is
preserved and reported instead of executing graph-supplied code. Future macro or
query syntax remains readable source, with a build warning. It is not evaluated.

Only the already-exported graph is read. Missing/private targets stay unavailable;
the converter never consults your private Logseq database to fill them in. A page
linked as a property value may have its exported title available without its page
body. Internal built-in schema pages are not exposed as garden pages.

Unresolved targets, missing attachments, unsupported links, and equation conversion
errors appear in `dist-report.json` outside the deployed directory. Unsupported
Transit data and lost block trees fail the build. This converter targets the DB
export format in the checked-out Logseq 2.0.1, not the older Markdown-graph export.
The small Transit reader follows https://github.com/cognitect/transit-format and
only supports the types needed by this export; it deliberately rejects new types.

## Site logo

`branding/logo.svg` is the editable vector version of the “a” mark, with outlined
lettering so its appearance does not depend on installed fonts. `branding/logo.png`
is the 512-pixel PNG. The build copies these to a hashed sidebar/SVG favicon asset,
`dist/static/img/logo.png`, and `dist/favicon.png`; the PNG also serves as the touch
icon and social image. `static/img/logo.png` in the source export has been updated
too, but **the converter's branding directory is the source of truth**. A later
Logseq export cannot replace the identity of the built site.

## Pre-commit hook

The local hook delegates to tracked `.githooks/pre-commit`. On a new clone, install
it with `./install-hooks.sh`. The installer backs up an existing hook as
`.git/hooks/pre-commit.before-static-garden` and refuses to overwrite that backup.

The old hook patched `index.html`, compressed assets in place, and used `git add`
on all assets. The replacement does none of those operations. For relevant
staged changes it:

1. Copies the **Git index** into a temporary directory (preserving partial staging).
2. Verifies that the staged commit contains the complete exporter and its inputs.
3. Checks that the local venv has the staged dependency versions, without downloads.
4. Builds that exact staged snapshot into temporary output and reports failures.

Nothing is auto-staged or written to the working tree, and your normal `dist/`
is not replaced. Documentation-only commits skip the build. Run `./build-static.sh`
once before committing to initialize the local venv, and stage the converter files
along with the export before the first commit using this pipeline. Cloudflare
continues to build using the command/output settings you already configured.
The old compression and patch scripts remain available for deliberate manual use.

## Customize

Edit `site.json` for the home page, navigation, title, description, language, and
canonical domain. Content continues to come from Logseq. Edit `garden.css` for the
Logseq-inspired dark sidebar and outline appearance; `garden.js` handles search and
old bookmarks. The build uses UUID suffixes to avoid collisions between page slugs.
Renaming a page also changes its slug; legacy UUID hash bookmarks still resolve.

## Verify

```sh
.venv-static/bin/python -m unittest discover -s static-garden -p 'test_*.py' -v
```

The builder also verifies that every exported block belonging to a rendered page
was rendered. `dist-report.json` records page/block/asset/equation counts and the
homepage payload sizes.
