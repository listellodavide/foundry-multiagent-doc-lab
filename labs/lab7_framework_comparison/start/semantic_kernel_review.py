"""Semantic Kernel concurrent-orchestration implementation for Lab 7."""

import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(HERE))

from common import DOMAINS, approve, merge_facts  # noqa: E402

from shared import config, pdf  # noqa: E402
from shared.clients import parse_model, save_run, timed  # noqa: E402
from shared.policy import build_record  # noqa: E402
from shared.schema import DecisionRecord, KeyFacts  # noqa: E402
from shared.vision import extract_profile_from_scan  # noqa: E402


async def run_review() -> DecisionRecord:
    # TODO 1: run three native SK agents concurrently and preserve the common result contract
    raise NotImplementedError("TODO 1: see the lab README")


async def main() -> None:
    with timed() as timing:
        record = await run_review()
    save_run("lab7_semantic_kernel", "7b. Semantic Kernel concurrent orchestration",
             timing["seconds"], record)


if __name__ == "__main__":
    asyncio.run(main())
