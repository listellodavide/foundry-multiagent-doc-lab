@echo off
setlocal EnableExtensions
cd /d "%~dp0" || exit /b 1

for %%E in (langgraph semantic-kernel autogen durable) do (
    if not exist ".venvs\%%E\Scripts\python.exe" (
        echo [SETUP] Creating Python 3.14 environment: %%E
        py -3.14 -m venv ".venvs\%%E" || exit /b 1
    )
    echo [SETUP] Installing %%E dependencies...
    ".venvs\%%E\Scripts\python.exe" -m pip install --disable-pip-version-check --quiet -r "requirements-%%E.txt" || exit /b 1
)

echo [PASS] Extension environments are ready.
