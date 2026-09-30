"""Lab 3 - Plan, execute, reflect.

Technique: three roles instead of one. A planner turns the policy into a typed plan
(which document answers which rule), an extractor fills the key facts following that plan,
and a critic checks every fact against the page it came from and sends wrong ones back
(at most two correction rounds). The decision itself is computed in code from the facts
(shared.policy.judge), because arithmetic and date comparisons are not a job for a model.

Run from the repo root:  python labs/lab3_plan_reflect/solution/plan_reflect.py
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agent_framework import Agent  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from shared import pdf  # noqa: E402
from shared.clients import chat_client, response_value, save_run, timed  # noqa: E402
from shared.policy import RULES, build_record, policy_text  # noqa: E402
from shared.schema import KeyFacts  # noqa: E402
from shared.vision import extract_profile_from_scan  # noqa: E402

MAX_ROUNDS = 2


class PlanStep(BaseModel):
    rule_id: str
    fact_fields: list[str] = Field(description="KeyFacts fields this rule needs")
    documents: list[str] = Field(description="Packet files that should contain the facts")
    what_to_look_for: str


class Plan(BaseModel):
    steps: list[PlanStep]


class FactCheck(BaseModel):
    field: str
    verdict: Literal["correct", "wrong", "not_in_source"]
    correct_value: str | None = Field(description="The value as written in the source, if wrong")
    reason: str


class Critique(BaseModel):
    checks: list[FactCheck]


def planned_files(plan: Plan) -> list[str]:
    """Text documents named in the plan that really exist; all text documents if the plan names none.
    A planner can invent file names, so its output is filtered, never trusted."""
    text_docs = {d["file"] for d in pdf.list_documents() if d["has_text_layer"]}
    named = {f for step in plan.steps for f in step.documents} & text_docs
    return sorted(named or text_docs)


async def make_plan(client) -> Plan:
    # TODO 1: a planner agent maps each rule to fact fields and documents (structured output Plan)
    raise NotImplementedError("TODO 1: see the lab README")


async def extract_facts(client, plan: Plan, feedback: str = "") -> KeyFacts:
    # TODO 2: the extractor reads only the documents the plan names and returns KeyFacts
    raise NotImplementedError("TODO 2: see the lab README")


async def critique(client, plan: Plan, facts: KeyFacts) -> Critique:
    # TODO 3: a critic compares each non-null fact with the source text and flags wrong ones
    raise NotImplementedError("TODO 3: see the lab README")


async def main() -> None:
    client = chat_client()
    with timed() as t:
        plan = await make_plan(client)
        print("Plan:")
        for step in plan.steps:
            print(f"  {step.rule_id}: {step.fact_fields} from {step.documents}")

        # TODO 4: extract, critique, and re-extract with the critic's feedback, at most MAX_ROUNDS times
        raise NotImplementedError("TODO 4: see the lab README")

        vendor = await asyncio.to_thread(extract_profile_from_scan)
        record = build_record(facts, vendor)
    for f in record.findings:
        print(f"  {f.rule_id} {f.status:7} {RULES[f.rule_id][0][:60]}")
    save_run("lab3", "3. Planner + extractor + critic, code judge", t["seconds"], record)


if __name__ == "__main__":
    asyncio.run(main())
