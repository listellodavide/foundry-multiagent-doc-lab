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
    # >>> TODO 1: build a persisted supervisor graph with a human approval node
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import END, START, StateGraph

    async def compliance_team(state: ReviewState) -> ReviewState:
        facts = await asyncio.gather(extract_domain("contract"), extract_domain("security"))
        return {"facts": facts}

    async def operations_team(state: ReviewState) -> ReviewState:
        facts, profile = await asyncio.gather(
            extract_domain("finance"), asyncio.to_thread(extract_profile_from_scan))
        return {"facts": [facts], "profile": profile}

    async def root_supervisor(state: ReviewState) -> ReviewState:
        return {"record": build_record(merge_facts(state["facts"]), state["profile"])}

    async def human_gate(state: ReviewState) -> ReviewState:
        return {"record": await approve(state["record"], auto="--auto" in sys.argv)}

    graph = StateGraph(ReviewState)
    graph.add_node("compliance_supervisor", compliance_team)
    graph.add_node("operations_supervisor", operations_team)
    graph.add_node("root_supervisor", root_supervisor)
    graph.add_node("human_gate", human_gate)
    graph.add_edge(START, "compliance_supervisor")
    graph.add_edge(START, "operations_supervisor")
    graph.add_edge("compliance_supervisor", "root_supervisor")
    graph.add_edge("operations_supervisor", "root_supervisor")
    graph.add_edge("root_supervisor", "human_gate")
    graph.add_edge("human_gate", END)
    return graph.compile(checkpointer=InMemorySaver())
    # <<< TODO 1


async def run_review() -> DecisionRecord:
    result = await build_graph().ainvoke({}, {"configurable": {"thread_id": "vendor-review"}})
    return result["record"]


async def main() -> None:
    with timed() as timing:
        record = await run_review()
    save_run("lab7_langgraph", "7a. LangGraph hierarchical supervisor", timing["seconds"], record)


if __name__ == "__main__":
    asyncio.run(main())
