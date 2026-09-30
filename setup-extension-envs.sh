#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

if command -v python3.14 >/dev/null 2>&1; then
    PYTHON=python3.14
elif command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 14))'; then
    PYTHON=python3
else
    echo "[FAIL] Python 3.14 was not found." >&2
    exit 1
fi

for environment in langgraph semantic-kernel autogen durable; do
    venv=".venvs/$environment"
    if [ ! -x "$venv/bin/python" ]; then
        echo "[SETUP] Creating Python 3.14 environment: $environment"
        "$PYTHON" -m venv "$venv"
    fi
    echo "[SETUP] Installing $environment dependencies..."
    "$venv/bin/python" -m pip install --disable-pip-version-check --quiet -r "requirements-$environment.txt"
done

echo "[PASS] Extension environments are ready."
