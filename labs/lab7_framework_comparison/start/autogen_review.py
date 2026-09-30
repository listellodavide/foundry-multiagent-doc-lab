"""AutoGen network/team lifecycle implementation for Lab 7."""

import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(HERE))

from common import DOMAINS, approve  # noqa: E402

from shared import config, pdf  # noqa: E402
from shared.clients import parse_model, save_run, timed  # noqa: E402
from shared.schema import DecisionRecord  # noqa: E402


async def run_review() -> DecisionRecord:
    # TODO 1: build and run a bounded native AutoGen selector team
    raise NotImplementedError("TODO 1: see the lab README")


async def main() -> None:
    with timed() as timing:
        record = await run_review()
    save_run("lab7_autogen", "7c. AutoGen networked selector team", timing["seconds"], record)


if __name__ == "__main__":
    asyncio.run(main())
