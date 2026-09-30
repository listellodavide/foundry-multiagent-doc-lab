"""October 2026 workshop setup check: verify prerequisites before attending.

    python setup_check.py            # full check, 2 small model calls
    python setup_check.py --offline  # everything except Azure
"""

import asyncio
import importlib
import subprocess
import sys

OFFLINE = "--offline" in sys.argv


def ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")
    sys.exit(1)


def main() -> None:
    if not (3, 12) <= sys.version_info[:2] <= (3, 14):
        fail(f"Python {sys.version.split()[0]}: use 3.12, 3.13 or 3.14")
    ok(f"Python {sys.version.split()[0]}")

    for module in ["agent_framework", "agent_framework.foundry", "agent_framework.orchestrations", "azure.ai.projects",
                   "azure.identity", "azure.ai.evaluation", "fastmcp", "mcp", "pymupdf", "pydantic", "dotenv"]:
        try:
            importlib.import_module(module)
        except ImportError as e:
            fail(f"cannot import {module} ({e}): run pip install -r requirements.txt")
    ok("packages installed")

    subprocess.run([sys.executable, "data/generate_packet.py"], check=True, capture_output=True)
    from shared.pdf import list_documents

    docs = list_documents()
    if len(docs) != 6:
        fail(f"expected 6 packet PDFs, found {len(docs)}")
    ok("onboarding packet generated (6 PDFs, 1 scanned)")

    result = subprocess.run([sys.executable, "score.py", "data/golden/decision_record.json"], capture_output=True, text=True)
    if "100.0" not in result.stdout:
        fail(f"scorer self-test failed:\n{result.stdout}{result.stderr}")
    ok("scorer self-test")

    if OFFLINE:
        print("\nOffline checks passed. Run without --offline once 'az login' works.")
        sys.exit(0)

    from shared import config

    config.require_endpoint()
    ok(f".env: {config.PROJECT_ENDPOINT} / {config.MODEL}")


    async def agent_call() -> str:
        from agent_framework import Agent

        from shared.clients import chat_client

        agent = Agent(client=chat_client(), name="check", instructions="Reply with the single word READY.")
        return (await agent.run("Are you ready?")).text


    try:
        ok(f"Agent Framework -> Foundry: {asyncio.run(agent_call()).strip()[:20]}")
        from shared.vision import extract_profile_from_scan

        profile = extract_profile_from_scan()
        ok(f"vision on the scanned page: {profile.legal_name} / {profile.signatory}")
        from shared.clients import project_client

        with project_client() as project:
            agents = list(project.agents.list())
        ok(f"Foundry Agent Service reachable ({len(agents)} agent(s) in the project)")
    except Exception as e:
        fail(f"Azure call failed ({type(e).__name__}): run 'az login', check the Foundry User role "
             f"on the project and the model deployment name. Detail: {e}")

    print("\nAll checks passed. See you at the workshop.")


if __name__ == "__main__":
    main()
