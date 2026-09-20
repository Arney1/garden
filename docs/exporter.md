# Updating the exporter

`garden` owns the content and deployment. `logseq-static-garden` owns rendering,
search, the graph, browser assets, and renderer tests.

Local source checkouts:

```text
/home/arney1/dev/projects/
├── garden/                 # personal website
└── logseq-static-garden/   # reusable exporter
```

## Normal publishing

Export public pages into `garden`, stage the changes, commit, and push. The build
command stays `./build-static.sh`; Cloudflare Pages still publishes `dist`.
There is no patching step and no exporter update required after each export.

Your site settings are in `site.json` and your logos are in `branding/`. The
exporter's generic defaults and sample notes do not replace them.

## Work on the renderer

Make changes in the **separate exporter checkout**, not under this repository's
`vendor/` directory. Build its fictional example, run its tests, and commit the
change there. Then, from this repository:

```sh
python3 tools/exporter.py update ../logseq-static-garden
./build-static.sh
```

To select an older release or commit explicitly:

```sh
python3 tools/exporter.py update ../logseq-static-garden --revision <tag-or-commit>
```

The updater requires a clean exporter checkout, copies the selected Git commit,
and records its commit ID and SHA-256 file checksums. It refuses to overwrite
edits made inside the current snapshot. It never changes your content or branding,
and does not stage, commit, or push anything.

Review the build, then stage **both `vendor/logseq-static-garden/` and
`exporter.lock.json`** and commit them together. The snapshot is intentionally kept
in Git so Cloudflare needs no submodule configuration, sibling directory, or
credentials to a second repository. It includes the license notices and credits.

The hashes detect mismatched or accidentally edited files; they are not a signature
or an audit of the upstream code. Only update from a source you trust.

## Local checks

```sh
python3 tools/exporter.py verify
.venv-static/bin/python -m unittest discover -s tools -p 'test_*.py' -v
.venv-static/bin/python -m unittest discover -s vendor/logseq-static-garden/static-garden -p 'test_*.py' -v
```

`./install-hooks.sh` installs the dispatcher. An existing dispatcher follows the
updated tracked hook automatically. The hook checks a temporary copy of the Git
index, so unstaged content cannot hide a broken staged build. It neither installs
dependencies nor changes your working tree, index, or preview output.

## Repository split

The new exporter starts with a clean history and credits existing contributions
in `AUTHORS.md`. It contains no personal graph export, attachments, screenshots,
or personal logo. The old combined history remains in this garden repository.
No GitHub repository rename or history rewrite is needed for this layout.

When publishing the new exporter repository, point contributors to it and link it
from this README. Existing merged PR attribution remains available in this repo.
