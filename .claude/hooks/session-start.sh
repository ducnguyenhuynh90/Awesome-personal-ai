#!/bin/bash
# SessionStart hook for Claude Code cloud sessions: installs Robin (editable) + test deps so
# `robin ...` commands and `python -m pytest` work immediately. Synchronous; skips when nothing changed.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

# pip installs into the system Python, so keep the hash file in that Python's package directory.
pyhashes="$(python3 -I -c 'import sysconfig; print(sysconfig.get_path("purelib"))')/.session-start.sha256"
if ! sha256sum --check --status "$pyhashes" 2>/dev/null; then
  rm -f "$pyhashes"
  python3 -m pip install --quiet --disable-pip-version-check -e '.[dev]'
  sha256sum .claude/hooks/session-start.sh pyproject.toml > "$pyhashes" || rm -f "$pyhashes"
fi

# Every session: make the repo importable for scripts run from anywhere.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PYTHONPATH=\"${CLAUDE_PROJECT_DIR:-$PWD}\"" >> "$CLAUDE_ENV_FILE"
fi
