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
    # >>> TODO 1: upload the five text packet PDFs and the policy PDF, build a vector store, wait until indexed
    # Register each resource immediately so partial uploads and indexing failures are cleaned up.
    with ExitStack() as cleanup:
        file_ids = []
        # The image-only profile is read by vision; File Search cannot index its text.
        text_packet = [path for path in sorted(config.PACKET_DIR.glob("*.pdf"))
                       if path.name != "06_company_profile_scan.pdf"]
        for path in text_packet + [config.POLICY_PDF]:
            with open(path, "rb") as handle:
                file_id = openai_client.files.create(file=handle, purpose="assistants").id
            file_ids.append(file_id)
            cleanup.callback(openai_client.files.delete, file_id=file_id)
        store = openai_client.vector_stores.create(name="carpathia-onboarding-packet", file_ids=file_ids)
        cleanup.callback(openai_client.vector_stores.delete, vector_store_id=store.id)
        for _ in range(60):
            current = openai_client.vector_stores.retrieve(vector_store_id=store.id)
            if current.status == "completed":
                if current.file_counts.failed:
                    raise RuntimeError("some packet files failed to index")
                break
            if current.status in {"failed", "expired"}:
                raise RuntimeError(f"vector store indexing {current.status}")
            time.sleep(2)
        else:
            raise TimeoutError("vector store indexing did not complete within 120 seconds")
        print(f"Indexed {len(file_ids)} files into vector store {store.id}")
        cleanup.pop_all()  # Ownership transfers to main after successful indexing.
        return file_ids, store.id
    # <<< TODO 1


def main() -> None:
    with timed() as t, project_client() as project, project.get_openai_client() as openai_client:
        file_ids, store_id = upload_packet(openai_client)
        with ExitStack() as cleanup:
            for file_id in file_ids:
                cleanup.callback(openai_client.files.delete, file_id=file_id)
            cleanup.callback(openai_client.vector_stores.delete, vector_store_id=store_id)
            # >>> TODO 2: read the scanned company profile with vision (shared.vision)
            profile = extract_profile_from_scan()
            print(f"Vision read the scanned profile: {profile.model_dump()}")
            # <<< TODO 2

            # >>> TODO 3: create a prompt agent version with File Search and Code Interpreter
            agent = project.agents.create_version(
                agent_name=f"{AGENT_NAME}-{uuid4().hex[:8]}",
                definition=PromptAgentDefinition(
                    model=config.MODEL,
                    instructions=INSTRUCTIONS,
                    tools=[
                        FileSearchTool(vector_store_ids=[store_id]),
                        CodeInterpreterTool(container=AutoCodeInterpreterToolParam()),
                    ],
                ),
            )
            cleanup.callback(project.agents.delete_version, agent_name=agent.name, agent_version=agent.version)
            print(f"Created {agent.name} v{agent.version}")
            # <<< TODO 3

            # >>> TODO 4: run the agent through the Responses API and parse the JSON record
            response = openai_client.responses.create(
                input=("Process the Carpathia Localization onboarding packet. Vendor profile read "
                       f"from the scanned page: {profile.model_dump_json()}"),
                extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
            )
            record = parse_model(response.output_text, DecisionRecord)
            # <<< TODO 4
        print("Cleaned up agent version, vector store and uploaded files")
    save_run("lab2", "2. Hosted agent: File Search + Code Interp. + vision", t["seconds"], record)


if __name__ == "__main__":
    main()
