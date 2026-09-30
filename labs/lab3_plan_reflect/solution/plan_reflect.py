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
    # >>> TODO 1: a planner agent maps each rule to fact fields and documents (structured output Plan)
    planner = Agent(client=client, name="planner", instructions=(
        "You plan document reviews. Given a policy and a list of documents, produce one step per rule: "
        "the KeyFacts fields it needs, the documents that should contain them, and what to look for. "
        f"KeyFacts fields: {list(KeyFacts.model_fields)}"))
    response = await planner.run(
        f"Policy:\n{policy_text()}\n\nDocuments:\n{json.dumps(pdf.list_documents())}",
        options={"response_format": Plan})
    return response_value(response, Plan)
    # <<< TODO 1


async def extract_facts(client, plan: Plan, feedback: str = "") -> KeyFacts:
    # >>> TODO 2: the extractor reads only the documents the plan names and returns KeyFacts
    files = planned_files(plan)
    corpus = "\n\n".join(pdf.document_text(f) for f in files)
    extractor = Agent(client=client, name="extractor", instructions=(
        "Extract the requested facts exactly as written in the documents. Dates as ISO 8601, amounts "
        "as numbers, names as written. Use null when a fact is not present. Watch for look-alike values: "
        "a data-subject deadline is not a breach deadline, a vulnerability scan is not a penetration test, "
        "professional indemnity is not cyber liability."))
    prompt = f"Plan:\n{plan.model_dump_json()}\n\nDocuments:\n{corpus}"
    if feedback:
        prompt += f"\n\nA reviewer found these problems in your previous answer. Fix them:\n{feedback}"
    response = await extractor.run(prompt, options={"response_format": KeyFacts})
    return response_value(response, KeyFacts)
    # <<< TODO 2


async def critique(client, plan: Plan, facts: KeyFacts) -> Critique:
    # >>> TODO 3: a critic compares each non-null fact with the source text and flags wrong ones
    sources = {f: pdf.document_text(f) for f in planned_files(plan)}
    critic = Agent(client=client, name="critic", instructions=(
        "You verify extracted facts against source documents. For every field, say whether the value "
        "is correct, wrong (give the value as written in the source), or not in the source. Be strict: "
        "a value from a different clause or a look-alike field is wrong."))
    response = await critic.run(
        f"Facts:\n{facts.model_dump_json()}\n\nSources:\n{json.dumps(sources)}",
        options={"response_format": Critique})
    return response_value(response, Critique)
    # <<< TODO 3


async def main() -> None:
    client = chat_client()
    with timed() as t:
        plan = await make_plan(client)
        print("Plan:")
        for step in plan.steps:
            print(f"  {step.rule_id}: {step.fact_fields} from {step.documents}")

        # >>> TODO 4: extract, critique, and re-extract with the critic's feedback, at most MAX_ROUNDS times
        facts = await extract_facts(client, plan)
        for round_no in range(1, MAX_ROUNDS + 1):
            review = await critique(client, plan, facts)
            wrong = [c for c in review.checks if c.verdict == "wrong"]
            print(f"Round {round_no}: critic flagged {len(wrong)} fact(s): {[c.field for c in wrong]}")
            if not wrong:
                break
            feedback = "\n".join(f"- {c.field}: should be {c.correct_value} ({c.reason})" for c in wrong)
            facts = await extract_facts(client, plan, feedback)
        # <<< TODO 4

        vendor = await asyncio.to_thread(extract_profile_from_scan)
        record = build_record(facts, vendor)
    for f in record.findings:
        print(f"  {f.rule_id} {f.status:7} {RULES[f.rule_id][0][:60]}")
    save_run("lab3", "3. Planner + extractor + critic, code judge", t["seconds"], record)


if __name__ == "__main__":
    asyncio.run(main())
