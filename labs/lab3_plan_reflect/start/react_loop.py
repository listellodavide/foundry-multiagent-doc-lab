"""Lab 3 extension - explicit, bounded Plan-Act-Observe (ReAct-style) review."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agent_framework import Agent

from shared import pdf
from shared.clients import chat_client, response_value, save_run, timed
from shared.policy import policy_text
from shared.react import Observation, ReActAction, run_react
from shared.schema import DecisionRecord
from shared.vision import extract_profile_from_scan

MAX_STEPS = 12


def list_documents() -> str:
    return json.dumps(pdf.list_documents())


def read_document(file: str) -> str:
    return pdf.document_text(file)


def search_packet(query: str) -> str:
    return json.dumps(pdf.search_text(query))


def read_scanned_profile() -> str:
    return extract_profile_from_scan().model_dump_json()


async def choose(client, goal: str, observations: list[Observation]) -> ReActAction:
    # TODO 1: ask a controller for exactly one allowlisted next action
    raise NotImplementedError("TODO 1: see the lab README")


async def run() -> tuple[DecisionRecord, list[Observation]]:
    client = chat_client()

    async def next_action(goal: str, observations: list[Observation]) -> ReActAction:
        return await choose(client, goal, observations)

    # TODO 2: run the bounded loop with only registered tools
    raise NotImplementedError("TODO 2: see the lab README")


async def main() -> None:
    with timed() as timing:
        record, trace = await run()
    for observation in trace:
        print(f"{observation.step}. {observation.action}: {observation.content[:100]}")
    save_run("lab3_react", "3b. Bounded Plan-Act-Observe", timing["seconds"], record)


if __name__ == "__main__":
    asyncio.run(main())
