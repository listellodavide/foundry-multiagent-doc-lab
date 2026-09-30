"""Lab 0 - identify agentic building blocks and implement a bounded agent."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agent_framework import Agent, tool
from pydantic import BaseModel

from shared import pdf
from shared.clients import chat_client, response_value, save_run, timed
from shared.policy import policy_text
from shared.schema import DecisionRecord


class AgenticComponents(BaseModel):
    goal: str
    model: str
    tools: list[str]
    state: str
    guardrails: list[str]
    evaluator: str
    human_authority: str


def classify_workload(known_steps: bool, uncertain_navigation: bool,
                      judgement_required: bool) -> Literal["deterministic", "agentic", "hybrid"]:
    if known_steps and not uncertain_navigation and not judgement_required:
        return "deterministic"
    if not known_steps and uncertain_navigation and judgement_required:
        return "agentic"
    return "hybrid"


def components() -> AgenticComponents:
    # TODO 1: make every component and control boundary explicit
    raise NotImplementedError("TODO 1: see the lab README")


@tool(approval_mode="never_require", max_invocations=1)
def list_documents() -> str:
    """List the onboarding documents."""
    return json.dumps(pdf.list_documents())


@tool(approval_mode="never_require", max_invocations=8)
def read_document(file: str) -> str:
    """Read a packet PDF with page markers."""
    try:
        return pdf.document_text(file)
    except (FileNotFoundError, ValueError) as exc:
        return f"ERROR: {exc}"


async def run() -> DecisionRecord:
    # TODO 2: create and run the smallest useful bounded agent
    raise NotImplementedError("TODO 2: see the lab README")


async def main() -> None:
    print(components().model_dump_json(indent=2))
    with timed() as timing:
        record = await run()
    save_run("lab0", "0. Agentic foundations", timing["seconds"], record)


if __name__ == "__main__":
    asyncio.run(main())
