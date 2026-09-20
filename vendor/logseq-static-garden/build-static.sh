#!/usr/bin/env bash
set -euo pipefail
engine_root="$(cd -- "$(dirname -- "$0")" && pwd)"
venv="$engine_root/.venv-static"
if [[ ! -x "$venv/bin/python" ]]; then
  python3 -m venv "$venv"
fi
"$venv/bin/python" -m pip install --disable-pip-version-check --quiet -r "$engine_root/static-garden/requirements.txt"
exec "$venv/bin/python" "$engine_root/static-garden/build.py" "$@"
