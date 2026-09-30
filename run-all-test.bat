@echo off
setlocal EnableExtensions

rem Run from this script's directory so it works when launched from Explorer or another folder.
cd /d "%~dp0" || exit /b 1

set "VENV_PYTHON=.venv\Scripts\python.exe"
set "VENV_RUFF=.venv\Scripts\ruff.exe"
set "VENV_PYRIGHT=.venv\Scripts\pyright.exe"
set "VENV_COVERAGE=.venv\Scripts\coverage.exe"
if defined TEMP (
    set "PYTEST_BASETEMP=%TEMP%\foundry-multiagent-doc-lab-pytest-%RANDOM%-%RANDOM%"
) else (
    set "PYTEST_BASETEMP=%CD%\.pytest-tmp"
)

if not exist "%VENV_PYTHON%" (
    echo [SETUP] Creating Python 3.14 environment in .venv...
    py -3.14 -m venv .venv || goto :failed
)

echo [SETUP] Installing development dependencies...
"%VENV_PYTHON%" -m pip install --disable-pip-version-check --quiet -r requirements-dev.txt || goto :failed

echo [1/7] Running unit tests...
"%VENV_PYTHON%" -m pytest --basetemp="%PYTEST_BASETEMP%" -q || goto :failed

echo [2/7] Measuring statement and branch coverage...
"%VENV_COVERAGE%" erase || goto :failed
"%VENV_COVERAGE%" run -m pytest --basetemp="%PYTEST_BASETEMP%" -q || goto :failed
"%VENV_COVERAGE%" report || goto :failed

echo [3/7] Running Ruff...
"%VENV_RUFF%" check . || goto :failed

echo [4/7] Running Pyright...
"%VENV_PYRIGHT%" || goto :failed

echo [5/7] Checking installed dependencies...
"%VENV_PYTHON%" -m pip check || goto :failed

echo [6/7] Running workshop setup checks offline...
"%VENV_PYTHON%" setup_check.py --offline || goto :failed

echo [7/7] Running the complete offline verifier...
"%VENV_PYTHON%" -m tools.verify_offline || goto :failed

echo.
echo [PASS] All tests and checks passed.
if exist "%PYTEST_BASETEMP%" rmdir /s /q "%PYTEST_BASETEMP%"
exit /b 0

:failed
set "FAIL_CODE=%errorlevel%"
if exist "%PYTEST_BASETEMP%" rmdir /s /q "%PYTEST_BASETEMP%"
echo.
echo [FAIL] A test or check failed. Exit code: %FAIL_CODE%
exit /b %FAIL_CODE%
