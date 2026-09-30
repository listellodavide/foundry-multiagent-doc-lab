#!/usr/bin/env sh
set -eu

# Run from this script's directory so it works from any current directory.
SCRIPT_DIR=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

VENV_PYTHON=".venv/bin/python"
VENV_RUFF=".venv/bin/ruff"
VENV_PYRIGHT=".venv/bin/pyright"
VENV_COVERAGE=".venv/bin/coverage"
PYTEST_BASETEMP=$(mktemp -d "${TMPDIR:-/tmp}/foundry-multiagent-doc-lab-pytest.XXXXXX")

cleanup() {
    rm -rf "$PYTEST_BASETEMP"
}
trap cleanup EXIT HUP INT TERM

if [ ! -x "$VENV_PYTHON" ]; then
    echo "[SETUP] Creating Python 3.14 environment in .venv..."
    if command -v python3.14 >/dev/null 2>&1; then
        python3.14 -m venv .venv
    elif command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 14))'; then
        python3 -m venv .venv
    else
        echo "[FAIL] Python 3.14 was not found. Install it and run this script again." >&2
        exit 1
    fi
fi

echo "[SETUP] Installing development dependencies..."
"$VENV_PYTHON" -m pip install --disable-pip-version-check --quiet -r requirements-dev.txt

echo "[1/7] Running unit tests..."
"$VENV_PYTHON" -m pytest --basetemp="$PYTEST_BASETEMP" -q

echo "[2/7] Measuring statement and branch coverage..."
"$VENV_COVERAGE" erase
"$VENV_COVERAGE" run -m pytest --basetemp="$PYTEST_BASETEMP" -q
"$VENV_COVERAGE" report

echo "[3/7] Running Ruff..."
"$VENV_RUFF" check .

echo "[4/7] Running Pyright..."
"$VENV_PYRIGHT"

echo "[5/7] Checking installed dependencies..."
"$VENV_PYTHON" -m pip check

echo "[6/7] Running workshop setup checks offline..."
"$VENV_PYTHON" setup_check.py --offline

echo "[7/7] Running the complete offline verifier..."
"$VENV_PYTHON" -m tools.verify_offline

printf '\n[PASS] All tests and checks passed.\n'
