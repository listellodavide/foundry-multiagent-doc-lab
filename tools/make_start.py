"""Builds each lab's start/ folder from its solution/ folder.

In solution files, code between '# >>> TODO n: description' and '# <<< TODO n' is replaced by
the TODO comment and a NotImplementedError, keeping indentation. Everything else is copied.

    python tools/make_start.py
"""

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = re.compile(r"^(\s*)# >>> (TODO [^:]+): (.*)$")
END = re.compile(r"^\s*# <<< TODO")


def strip(source: str) -> str:
    out, skipping = [], False
    for line in source.splitlines():
        m = START.match(line)
        if m:
            indent, tag, text = m.groups()
            out += [f"{indent}# {tag}: {text}", f'{indent}raise NotImplementedError("{tag}: see the lab README")']
            skipping = True
        elif END.match(line):
            skipping = False
        elif not skipping:
            out.append(line)
    return "\n".join(out) + "\n"


def main() -> None:
    for solution in sorted(ROOT.glob("labs/*/solution")):
        start = solution.parent / "start"
        if start.exists():
            shutil.rmtree(start)
        start.mkdir()
        for file in solution.iterdir():
            if file.suffix == ".py":
                (start / file.name).write_text(strip(file.read_text()))
            elif file.is_file():
                shutil.copy(file, start / file.name)
        print(f"  {start.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
