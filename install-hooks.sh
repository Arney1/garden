#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
# Respect an existing custom hooks location rather than silently overriding it.
custom_hooks="$(git config --get core.hooksPath || true)"
if [[ -n "$custom_hooks" ]]; then
  echo "core.hooksPath is already set to $custom_hooks. Install .githooks/pre-commit there explicitly." >&2
  exit 1
fi
hook="$(git rev-parse --git-path hooks/pre-commit)"
mkdir -p -- "$(dirname -- "$hook")"
if [[ -f "$hook" ]] && ! grep -q 'garden hook dispatcher' "$hook"; then
  backup="${hook}.before-static-garden"
  if [[ -e "$backup" ]]; then
    echo "Refusing to overwrite existing hook backup: $backup" >&2
    exit 1
  fi
  cp -- "$hook" "$backup"
fi
cat > "$hook" <<'HOOK'
#!/usr/bin/env bash
# garden hook dispatcher; source is tracked in .githooks/pre-commit
set -euo pipefail
repo_root="$(git rev-parse --show-toplevel)"
exec bash "$repo_root/.githooks/pre-commit"
HOOK
chmod +x "$hook"
echo "Installed the static garden validator. The previous hook is preserved beside it if one existed."
