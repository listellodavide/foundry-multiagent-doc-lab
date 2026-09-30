"""Lab 4 - A workflow graph: fan-out to specialists, fan-in, conditional re-check.

Technique: deterministic orchestration with Agent Framework workflows. The graph, not a
model, decides the order: intake fans out to four specialists in parallel (contract,
security, finance, and a vision reader for the scanned profile), an aggregator merges their
facts and applies the policy in code, and a switch-case edge sends records with 'unknown'
rules to a re-check step before the final output. Every superstep is checkpointed.

Run from the repo root:  python labs/lab4_workflow/solution/workflow.py
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Never

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agent_framework import (  # noqa: E402
    Agent,
    Case,
    Default,
    Executor,
    FileCheckpointStorage,
    WorkflowBuilder,
    WorkflowContext,
    WorkflowViz,
    executor,
    handler,
)

from shared import config, pdf  # noqa: E402
from shared.messages import Packet, Partial  # noqa: E402
from shared.clients import chat_client, response_value, save_run, timed  # noqa: E402
from shared.policy import build_record  # noqa: E402
from shared.schema import DecisionRecord, KeyFacts, VendorProfile  # noqa: E402
from shared.vision import extract_profile_from_scan  # noqa: E402

RULE_FIELDS = {
    "R1": ["breach_notification_hours"], "R2": ["pen_test_date"], "R3": ["soc2_report_date"],
    "R4": ["insurance_cover_eur", "insurance_expiry"], "R5": ["payment_terms_days"],
    "R6": ["liability_cap_months"], "R7": ["invoice_subtotal", "invoice_vat", "invoice_total"],
    "R8": ["msa_signatory"],
}


def fact_agent(client, name: str) -> Agent:
    return Agent(client=client, name=name, instructions=(
        "Extract facts exactly as written in the documents you are given. Dates ISO 8601, amounts as "
        "numbers, names as written. Fill only the fields you are asked for; use null for everything "
        "else and for anything not present. Never guess."))


# A specialist executor wraps one agent, reads only its documents, returns only its fields.
class Specialist(Executor):
    def __init__(self, agent: Agent, documents: list[str], fields: list[str], id: str):
        super().__init__(id=id)
        self.agent, self.documents, self.fields = agent, documents, fields

    @handler
    async def extract(self, packet: Packet, ctx: WorkflowContext[Partial]) -> None:
        # >>> TODO 1: run the agent on self.documents only and send a Partial with only self.fields
        corpus = "\n\n".join(packet.texts[d] for d in self.documents)
        response = await self.agent.run(
            f"Fields to fill: {self.fields}\n\nDocuments:\n{corpus}", options={"response_format": KeyFacts})
        facts = response_value(response, KeyFacts).model_dump()
        print(f"  [{self.id}] {({k: facts[k] for k in self.fields})}")
        await ctx.send_message(Partial(source=self.id, facts={k: facts[k] for k in self.fields}))
        # <<< TODO 1


@executor(id="intake")
async def intake(packet_dir: str, ctx: WorkflowContext[Packet]) -> None:
    texts = {d["file"]: pdf.document_text(d["file"]) for d in pdf.list_documents() if d["has_text_layer"]}
    print(f"  [intake] {len(texts)} text documents from {Path(packet_dir).name}")
    await ctx.send_message(Packet(texts=texts))


@executor(id="profile_reader")
async def profile_reader(packet: Packet, ctx: WorkflowContext[Partial]) -> None:
    profile = await asyncio.to_thread(extract_profile_from_scan)
    print(f"  [profile_reader] {profile.model_dump()}")
    await ctx.send_message(Partial(source="profile_reader", vendor=profile.model_dump()))


@executor(id="aggregator")
async def aggregator(partials: list[Partial], ctx: WorkflowContext[DecisionRecord]) -> None:
    # >>> TODO 2: merge the partial facts and the vendor profile, then apply the policy in code
    facts, vendor = {}, {}
    for part in partials:
        facts.update({k: v for k, v in part.facts.items() if v is not None})
        vendor.update(part.vendor or {})
    record = build_record(KeyFacts(**{k: facts.get(k) for k in KeyFacts.model_fields}),
                          VendorProfile(**{k: vendor.get(k) for k in VendorProfile.model_fields}))
    print(f"  [aggregator] decision {record.decision}, unknown: "
          f"{[f.rule_id for f in record.findings if f.status == 'unknown']}")
    await ctx.send_message(record)
    # <<< TODO 2


class Rechecker(Executor):
    """Second chance for 'unknown' rules: one agent reads the whole packet for the missing fields only."""

    def __init__(self, agent: Agent):
        super().__init__(id="rechecker")
        self.agent = agent

    @handler
    async def recheck(self, record: DecisionRecord, ctx: WorkflowContext[Never, DecisionRecord]) -> None:
        missing = [f for x in record.findings if x.status == "unknown" for f in RULE_FIELDS[x.rule_id]]
        corpus = "\n\n".join(pdf.document_text(d["file"]) for d in pdf.list_documents() if d["has_text_layer"])
        response = await self.agent.run(f"Fields to fill: {missing}\n\nDocuments:\n{corpus}",
                                        options={"response_format": KeyFacts})
        found = {k: v for k, v in response_value(response, KeyFacts).model_dump().items() if k in missing and v is not None}
        print(f"  [rechecker] recovered {found}")
        merged = KeyFacts(**{**record.facts.model_dump(), **found})
        await ctx.yield_output(build_record(merged, record.vendor))


@executor(id="finalize")
async def finalize(record: DecisionRecord, ctx: WorkflowContext[Never, DecisionRecord]) -> None:
    await ctx.yield_output(record)


def build_workflow():
    client = chat_client()
    contract = Specialist(fact_agent(client, "contract"), ["01_msa.pdf"],
                          ["payment_terms_days", "liability_cap_months", "msa_signatory"], id="contract")
    security = Specialist(fact_agent(client, "security"),
                          ["02_dpa.pdf", "03_security_questionnaire.pdf", "04_insurance_certificate.pdf"],
                          ["breach_notification_hours", "pen_test_date", "soc2_report_date",
                           "insurance_cover_eur", "insurance_expiry"], id="security")
    finance = Specialist(fact_agent(client, "finance"), ["05_invoice.pdf"],
                         ["invoice_subtotal", "invoice_vat", "invoice_total"], id="finance")
    rechecker = Rechecker(fact_agent(client, "rechecker"))

    # >>> TODO 3: wire the graph: fan-out, fan-in, then a switch-case on 'unknown' findings
    specialists = [contract, security, finance, profile_reader]
    return (
        WorkflowBuilder(name="onboarding-desk", start_executor=intake,
                        checkpoint_storage=FileCheckpointStorage(str(config.OUT_DIR / "checkpoints")))
        .add_fan_out_edges(intake, specialists)
        .add_fan_in_edges(specialists, aggregator)
        .add_switch_case_edge_group(aggregator, [
            Case(condition=lambda r: any(f.status == "unknown" for f in r.findings), target=rechecker),
            Default(target=finalize),
        ])
        .build()
    )
    # <<< TODO 3


async def main() -> None:
    workflow = build_workflow()
    (config.OUT_DIR / "lab4_workflow.mmd").write_text(WorkflowViz(workflow).to_mermaid())
    print("Graph written to out/lab4_workflow.mmd (paste into any Mermaid viewer)")
    with timed() as t:
        result = await workflow.run(str(config.PACKET_DIR))
        record = result.get_outputs()[-1]
    print(json.dumps([(f.rule_id, f.status) for f in record.findings]))
    save_run("lab4", "4. Workflow: fan-out/fan-in + switch-case", t["seconds"], record)


if __name__ == "__main__":
    asyncio.run(main())
