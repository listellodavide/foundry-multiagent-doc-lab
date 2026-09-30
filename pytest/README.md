# Unit tests — October 2026 workshop

## Step-by-step: run everything on Windows

For a single-command run, use:

```powershell
.\run-all-test.bat
```

On macOS or Linux:

```bash
chmod +x run-all-test.sh
./run-all-test.sh
```

Both scripts create `.venv` with Python 3.14 when needed, install development dependencies,
and stop immediately if any test or check fails.
The launchers create a unique pytest directory under `%TEMP%` on Windows or `${TMPDIR:-/tmp}`
on macOS/Linux, then remove it when finished. No username or profile path is hardcoded. Direct
pytest commands use the repository-local `.pytest-tmp/` fallback configured in `pytest.ini`.

Open PowerShell in the repository root, then verify that you are in the right folder:

```powershell
Get-Location
Test-Path .\requirements-dev.txt
```

`Test-Path` must print `True`. Create the Python 3.14 environment if `.venv` does not exist:

```powershell
py -3.14 -m venv .venv
```

You may activate it, but activation is optional:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, continue with the explicit `.venv` Python commands below.
Install the exact development dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Run the complete unit suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The expected result is `126 passed`. Run the same suite with statement and branch coverage:

```powershell
.\.venv\Scripts\coverage.exe erase
.\.venv\Scripts\coverage.exe run -m pytest -q
.\.venv\Scripts\coverage.exe report
```

The report must finish with `100%`. `.coveragerc` makes coverage fail below 90%, so missing
coverage also produces a nonzero command exit code. To inspect coverage in a browser:

```powershell
.\.venv\Scripts\coverage.exe html
Start-Process .\htmlcov\index.html
```

Useful focused commands:

```powershell
# One test file
.\.venv\Scripts\python.exe -m pytest pytest\test_policy.py -v

# One exact test, with printed output visible
.\.venv\Scripts\python.exe -m pytest pytest\test_policy.py::test_golden_policy -v -s

# Stop on the first failure and show local variables
.\.venv\Scripts\python.exe -m pytest -x -vv --showlocals

# Re-run only tests that failed in the previous run
.\.venv\Scripts\python.exe -m pytest --lf -vv
```

Finally, run the static checks and offline workshop verifier:

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\pyright.exe
.\.venv\Scripts\python.exe setup_check.py --offline
.\.venv\Scripts\python.exe -m tools.verify_offline
```

The `pytest/` folder has no `__init__.py`, so it does not shadow the installed pytest package.
The suite generates its own PDF packet in a temporary directory. Azure clients and model
responses are mocked; running the tests requires no Azure sign-in and incurs no model costs.
The MCP test starts the local solution server and checks its tool discovery.

| File | Coverage |
| --- | --- |
| `test_policy.py` | All eight policy rules, thresholds, date windows, missing facts, decisions |
| `test_shared.py` | Scoring, saved outputs, JSON parsing, PDFs, vision refusals, configuration |
| `test_solutions.py` | Every solution/starter import, starter generation, mocked agent calls, uploads and cleanup, planning, workflow field isolation, MCP, handoff history, groundedness and variance |
| `test_coverage_edges.py` | Remaining positive/negative branches, conversation limits, CLI helpers, verifier failures and cleanup paths |
| `test_setup_check.py` | Offline/online readiness success and failures for Python, packages, documents, scoring and Azure calls |

Starter TODOs intentionally raise `NotImplementedError`; import validation does not complete
the exercises. Mocked solution tests check program behavior, not model accuracy. Run the
solutions against Foundry separately and use `python score.py` to measure their actual results.

Unit coverage proves deterministic program behavior under the tested inputs. It does not prove
that a live model will return the correct answer or that Azure quota and connectivity are available.
