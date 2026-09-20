# Contributing

## Local checks

```sh
./build-static.sh --source examples/minimal --output dist
.venv-static/bin/python -m unittest discover -s static-garden -p 'test_*.py' -v
python3 -m http.server 8000 --directory dist
```

Use Python 3.10+ and Node.js. The browser assets have no npm dependencies.
For layout or interaction changes, check a narrow phone viewport and desktop.
Python's preview server does not apply `_headers`; test changes to frame, script,
or attachment handling with those headers applied as well.

## Where changes go

- `static-garden/build.py`: rendering, asset handling, output documents, headers.
- `static-garden/transit_reader.py`: public-export decoding.
- `static-garden/garden.*`: outline layout, navigation, and search.
- `static-garden/graph*`: graph layout and viewer.
- `examples/minimal/`: fictional, reproducible build input.
- `vendor/katex/` and `licenses/`: the build-time bundle and dependency notices.

Keep fixes focused and add a regression test for parser or rendering bugs. For a
new media provider, validate its URLs and update the CSP alongside the renderer.
Do not enable raw graph HTML or execute JavaScript from an input export.

Please leave personal notes, attachments, custom branding, and deployment secrets
out of PRs. For a bug report, share the smallest public or fictional reproduction
you can. Your garden can use its own `site.json` and `branding/` without editing
this repository.

## Updating a consuming garden

Commit and test an exporter change first. A site that vendors this tool should
then update its pinned snapshot and review a full build before deployment. A local
exporter checkout is not a deployment dependency.
