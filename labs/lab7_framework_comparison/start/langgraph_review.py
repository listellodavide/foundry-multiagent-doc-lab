"""LangGraph hierarchical supervisor implementation for Lab 7."""

import asyncio
import operator
import sys
from pathlib import Path
from typing import Annotated, TypedDict

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(HERE))

from common import approve, extract_domain, merge_facts  # noqa: E402

from shared.clients import save_run, timed  # noqa: E402
from shared.policy import build_record  # noqa: E402
from shared.schema import DecisionRecord, KeyFacts, VendorProfile  # noqa: E402
from shared.vision import extract_profile_from_scan  # noqa: E402


class ReviewState(TypedDict, total=False):
    facts: Annotated[list[KeyFacts], operator.add]
    profile: VendorProfile
    record: DecisionRecord


def build_graph():
    # TODO 1: build a persisted supervisor graph with a human approval node
    raise NotImplementedError("TODO 1: see the lab README")


async def run_review() -> DecisionRecord:
    result = await build_graph().ainvoke({}, {"configurable": {"thread_id": "vendor-review"}})
    return result["record"]


async def main() -> None:
    with timed() as timing:
        record = await run_review()
    save_run("lab7_langgraph", "7a. LangGraph hierarchical supervisor", timing["seconds"], record)


if __name__ == "__main__":
    asyncio.run(main())
