#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
python3 tools/exporter.py verify
if [[ ! -x .venv-static/bin/python ]]; then
  python3 -m venv .venv-static
fi
.venv-static/bin/python -m pip install --disable-pip-version-check --quiet -r vendor/logseq-static-garden/static-garden/requirements.txt
exec .venv-static/bin/python vendor/logseq-static-garden/static-garden/build.py --source "$PWD" "$@"
