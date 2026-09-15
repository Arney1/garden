#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [[ ! -x .venv-static/bin/python ]]; then
  python3 -m venv .venv-static
fi
.venv-static/bin/python -m pip install --disable-pip-version-check --no-cache-dir --quiet -r static-garden/requirements.txt
exec .venv-static/bin/python static-garden/build.py "$@"
