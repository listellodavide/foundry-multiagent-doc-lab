"""Lab 5 (part 2) - Handoff between specialists, tools over MCP, a human in the conversation.

Technique: a coordinator agent talks to the procurement officer (you) and hands the
conversation to contract, security or finance specialists. All of them use the PDF tools
from pdf_mcp_server.py through MCP, not Python imports. When the review is complete a
writer agent turns the conversation into the DecisionRecord.

Run from the repo root:
    python labs/lab5_mcp_handoff/solution/desk.py          # you answer the agents
    python labs/lab5_mcp_handoff/solution/desk.py --auto   # scripted officer, for demos and scoring
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agent_framework import Agent, MCPStdioTool
from agent_framework.openai import OpenAIChatOptions
from agent_framework.orchestrations import HandoffAgentUserRequest, HandoffBuilder

from shared.clients import chat_client, response_value, save_run, timed
from shared.config import ONBOARDING_DATE
from shared.schema import DecisionRecord

SERVER = Path(__file__).with_name("pdf_mcp_server.py")
DONE = "REVIEW COMPLETE"
AUTO_REPLIES = [
    f"We want Carpathia Localization to start on {ONBOARDING_DATE}. Check every rule R1 to R8 and tell me what blocks it.",
    "Continue with the rules you have not checked yet.",
    "Anything else I need to know before I sign the purchase order?",
]

SPECIALIST_RULES = {
    "contract_specialist": ("R5, R6 and R8: payment terms and liability cap in 01_msa.pdf, and whether the MSA "
                            "signatory is the authorised signatory (use read_scanned_profile for 06)."),
    "security_specialist": ("R1 to R4: breach notice in 02_dpa.pdf, penetration test and SOC 2 in "
                            "03_security_questionnaire.pdf, cyber insurance in 04_insurance_certificate.pdf."),
    "finance_specialist": "R7: invoice arithmetic in 05_invoice.pdf. Always use check_invoice_math.",
    "identity_specialist": ("R8: compare the MSA signatory in 01_msa.pdf with the authorised "
                            "signatory returned by read_scanned_profile."),
}

SUPERVISOR_TEAMS = {
    "compliance_supervisor": ["contract_specialist", "security_specialist"],
    "operations_supervisor": ["finance_specialist", "identity_specialist"],
}


def build_desk(client, pdf_tools):
    # TODO 2: a coordinator, two supervisors and four specialists, all sharing the MCP tools
    raise NotImplementedError("TODO 2: see the lab README")

    # TODO 3: wire a two-level hierarchy and stop when the coordinator says DONE
    raise NotImplementedError("TODO 3: see the lab README")


async def converse(workflow, auto: bool) -> list[str]:
    transcript, replies = [], iter(AUTO_REPLIES)
    first = next(replies) if auto else input("Procurement officer: ")
    transcript.append(f"officer: {first}")

    async def drain(stream) -> list:
        pending = []
        async for event in stream:
            if event.type == "request_info":
                pending.append(event)
        return pending

    pending = await drain(workflow.run(first, stream=True))
    for _ in range(8):  # harness limit on conversation turns
        if not pending:
            break
        responses = {}
        for req in pending:
            if isinstance(req.data, HandoffAgentUserRequest):
                for msg in req.data.agent_response.messages:
                    if msg.text:
                        transcript.append(f"{msg.author_name}: {msg.text}")
                        print(f"\n{msg.author_name}: {msg.text}")
                answer = next(replies, "terminate") if auto else input("\nProcurement officer: ")
                transcript.append(f"officer: {answer}")
                responses[req.request_id] = (HandoffAgentUserRequest.terminate() if answer == "terminate"
                                             else HandoffAgentUserRequest.create_response(answer))
        pending = await drain(workflow.run(responses=responses, stream=True))
    return transcript


async def main(auto: bool) -> None:
    client = chat_client()
    with timed() as t:
        async with MCPStdioTool(name="pdf_desk", command=sys.executable, args=[str(SERVER)]) as pdf_tools:
            transcript = await converse(build_desk(client, pdf_tools), auto)
            # TODO 4: a writer agent turns the conversation into the DecisionRecord (it may re-read pages)
            raise NotImplementedError("TODO 4: see the lab README")
    save_run("lab5", "5. Handoff specialists + MCP tools + human", t["seconds"], record)


if __name__ == "__main__":
    asyncio.run(main(auto="--auto" in sys.argv))
