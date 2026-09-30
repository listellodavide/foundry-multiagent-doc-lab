"""Lab 1 - One agent, local tools.

Technique: a single Agent Framework agent that reads the packet through three function
tools (local PyMuPDF parsing) and returns a structured DecisionRecord.

Run from the repo root:  python labs/lab1_single_agent/solution/onboarding_agent.py
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Annotated

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agent_framework import Agent, tool
from pydantic import Field

from shared import pdf
from shared.clients import chat_client, response_value, save_run, timed
from shared.config import ONBOARDING_DATE
from shared.policy import policy_text
from shared.schema import DecisionRecord


# Three tools. Each does one thing, returns text, and cannot leave the packet folder.
@tool(approval_mode="never_require", max_invocations=5)
def list_documents() -> str:
    """List the PDF files in the onboarding packet, with page count and whether they have a text layer."""
    # >>> TODO 1a: return the packet listing as JSON (use pdf.list_documents)
    return json.dumps(pdf.list_documents())
    # <<< TODO 1a


@tool(approval_mode="never_require", max_invocations=20)
def read_document(
    file: Annotated[str, Field(description="File name exactly as returned by list_documents, e.g. 02_dpa.pdf")],
) -> str:
    """Return the text of one PDF, page by page, with '--- file pN ---' markers to cite."""
    # >>> TODO 1b: return pdf.document_text(file); turn errors into an 'ERROR: ...' string, never raise
    try:
        return pdf.document_text(file)
    except (FileNotFoundError, ValueError) as e:
        return f"ERROR: {e}"
    # <<< TODO 1b


@tool(approval_mode="never_require", max_invocations=3)
def read_policy() -> str:
    """Return the vendor onboarding policy: rules R1 to R8, onboarding date and decision rule."""
    return policy_text()


INSTRUCTIONS = f"""You are the vendor onboarding desk at Contoso Creative.
Onboarding date: {ONBOARDING_DATE}.
1. Call read_policy, then list_documents, then read every document.
2. Extract the vendor profile and the key facts. Dates in ISO 8601, amounts as numbers.
3. Check every rule R1 to R8. For each finding quote the evidence and cite 'file pN'.
4. If a fact is not readable (for example a scanned page without a text layer), use null
   and mark the rule 'unknown'. Never guess.
5. Apply the policy's decision rule and explain it in two to four sentences."""


async def run() -> DecisionRecord:
    # >>> TODO 2: Create the agent and run it with DecisionRecord as the response format.
    agent = Agent(
        client=chat_client(),
        name="onboarding-desk",
        instructions=INSTRUCTIONS,
        tools=[list_documents, read_document, read_policy],
    )
    response = await agent.run(
        "Process the Carpathia Localization onboarding packet and return the decision record.",
        options={"response_format": DecisionRecord},
    )
    return response_value(response, DecisionRecord)
    # <<< TODO 2


async def main() -> None:
    with timed() as t:
        record = await run()
    save_run("lab1", "1. Single agent + local PDF tools", t["seconds"], record)


if __name__ == "__main__":
    asyncio.run(main())
