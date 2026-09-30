"""Lab 2 - Hosted Foundry agent: File Search, Code Interpreter and vision.

Technique: the agent lives in Foundry Agent Service (azure-ai-projects 2.x). The PDFs are
uploaded into a vector store and searched server-side; Code Interpreter checks the invoice
arithmetic; the scanned company profile, which has no text layer and is invisible to File
Search, is read by a vision call first and handed to the agent as context.

Run from the repo root:  python labs/lab2_foundry_hosted/solution/hosted_desk.py
"""

import sys
import time
from contextlib import ExitStack
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from azure.ai.projects.models import (
    AutoCodeInterpreterToolParam,
    CodeInterpreterTool,
    FileSearchTool,
    PromptAgentDefinition,
)

from shared import config
from shared.clients import parse_model, project_client, save_run, timed
from shared.policy import policy_text
from shared.schema import DecisionRecord
from shared.vision import extract_profile_from_scan

AGENT_NAME = "onboarding-desk-hosted"

INSTRUCTIONS = f"""You are the vendor onboarding desk at Contoso Creative.
Policy:
{policy_text()}

Use file_search to find every fact in the uploaded packet; cite the file name for each finding.
Use the code interpreter to verify the invoice arithmetic (subtotal + VAT = total) instead of
doing it in your head. The vendor profile from the scanned page is given in the user message.
Use null for facts you cannot find and mark those rules 'unknown'. Never guess.
Answer with JSON only, matching this schema:
{DecisionRecord.model_json_schema()}"""


def upload_packet(openai_client) -> tuple[list[str], str]:
    # TODO 1: upload the five text packet PDFs and the policy PDF, build a vector store, wait until indexed
    raise NotImplementedError("TODO 1: see the lab README")


def main() -> None:
    with timed() as t, project_client() as project, project.get_openai_client() as openai_client:
        file_ids, store_id = upload_packet(openai_client)
        with ExitStack() as cleanup:
            for file_id in file_ids:
                cleanup.callback(openai_client.files.delete, file_id=file_id)
            cleanup.callback(openai_client.vector_stores.delete, vector_store_id=store_id)
            # TODO 2: read the scanned company profile with vision (shared.vision)
            raise NotImplementedError("TODO 2: see the lab README")

            # TODO 3: create a prompt agent version with File Search and Code Interpreter
            raise NotImplementedError("TODO 3: see the lab README")

            # TODO 4: run the agent through the Responses API and parse the JSON record
            raise NotImplementedError("TODO 4: see the lab README")
        print("Cleaned up agent version, vector store and uploaded files")
    save_run("lab2", "2. Hosted agent: File Search + Code Interp. + vision", t["seconds"], record)


if __name__ == "__main__":
    main()
