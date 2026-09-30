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

from agent_framework import Agent, MCPStdioTool  # noqa: E402
from agent_framework.orchestrations import HandoffAgentUserRequest, HandoffBuilder  # noqa: E402

from shared.clients import chat_client, response_value, save_run, timed  # noqa: E402
from shared.config import ONBOARDING_DATE  # noqa: E402
from shared.schema import DecisionRecord  # noqa: E402

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
}


def build_desk(client, pdf_tools):
    # >>> TODO 2: a coordinator and three specialists, all sharing the MCP tools
    # Handoff needs each agent to persist history per service call (Agent Framework 1.12+).
    handoff_ready = {"require_per_service_call_history_persistence": True}
    coordinator = Agent(client=client, name="coordinator", tools=pdf_tools, **handoff_ready,
                        description="Talks to the procurement officer and routes work to specialists.",
                        instructions=(
                            "You coordinate a vendor onboarding review. Call read_policy first. Hand off to the "
                            "specialist who owns each rule. When all eight rules have a verdict, summarise the "
                            f"verdicts with sources and end your message with '{DONE}'."))
    specialists = [
        Agent(client=client, name=name, tools=pdf_tools, **handoff_ready,
              description=f"Checks {scope.split(':')[0]}",
              instructions=(f"You own {scope} Read the pages before answering, quote the evidence and cite "
                            "'file pN'. Say 'unknown' if the document does not answer it. Then hand back to "
                            "the coordinator."))
        for name, scope in SPECIALIST_RULES.items()
    ]
    # <<< TODO 2

    # >>> TODO 3: handoff rules: coordinator <-> each specialist, and stop when the coordinator says DONE
    return (
        HandoffBuilder(name="onboarding_handoff", participants=[coordinator, *specialists],
                       termination_condition=lambda conv: bool(conv) and DONE in (conv[-1].text or ""))
        .with_start_agent(coordinator)
        .add_handoff(coordinator, specialists)
        .add_handoff(specialists[0], [coordinator])
        .add_handoff(specialists[1], [coordinator])
        .add_handoff(specialists[2], [coordinator])
        .build()
    )
    # <<< TODO 3


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
            # >>> TODO 4: a writer agent turns the conversation into the DecisionRecord (it may re-read pages)
            writer = Agent(client=client, name="writer", tools=pdf_tools, instructions=(
                "Turn a vendor review conversation into a decision record. Re-read a page when the "
                "conversation is unclear. Use null and 'unknown' for anything not established. Never guess."))
            response = await writer.run("\n".join(transcript), options={"response_format": DecisionRecord})
            record = response_value(response, DecisionRecord)
            # <<< TODO 4
    save_run("lab5", "5. Handoff specialists + MCP tools + human", t["seconds"], record)


if __name__ == "__main__":
    asyncio.run(main(auto="--auto" in sys.argv))
