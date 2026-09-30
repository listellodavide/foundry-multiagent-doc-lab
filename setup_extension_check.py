"""Readiness checks for the advanced third workshop day."""

import argparse
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENVIRONMENTS = {
    "langgraph": "import langgraph",
    "semantic-kernel": "import semantic_kernel",
    "autogen": "import autogen_agentchat; import autogen_ext",
    "durable": "import azure.functions; import azure.durable_functions",
}


def environment_python(name: str) -> Path:
    folder = ROOT / ".venvs" / name
    return folder / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def command_version(command: str) -> str | None:
    path = shutil.which(command)
    if not path:
        return None
    result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=15, check=False)
    return (result.stdout or result.stderr).strip()


def port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def main(offline: bool = False) -> None:
    failures: list[str] = []
    if sys.version_info[:2] != (3, 14):
        failures.append(f"runner is Python {sys.version_info.major}.{sys.version_info.minor}, expected 3.14")
    for name, statement in ENVIRONMENTS.items():
        python = environment_python(name)
        if not python.exists():
            display_path = python.relative_to(ROOT) if python.is_relative_to(ROOT) else python
            failures.append(f"missing {display_path}")
            continue
        result = subprocess.run([str(python), "-c", statement], capture_output=True, text=True,
                                timeout=30, check=False)
        if result.returncode:
            failures.append(f"{name} import failed: {result.stderr.strip().splitlines()[-1]}")
    core_tools = command_version("func")
    if not core_tools or not core_tools.startswith("4."):
        failures.append("Azure Functions Core Tools v4 was not found")
    if not command_version("azurite"):
        failures.append("Azurite was not found")
    elif not offline and not port_open("127.0.0.1", 10000):
        failures.append("Azurite is installed but its Blob endpoint is not listening on port 10000")
    if failures:
        raise SystemExit("Extension setup failed:\n- " + "\n- ".join(failures))
    print("Extension-day setup passed: Python 3.14, four environments, Core Tools and Azurite.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Do not require Azurite to be running")
    main(parser.parse_args().offline)
