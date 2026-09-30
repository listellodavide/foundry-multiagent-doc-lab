"""Configuration shared by every lab. Values come from the .env file at the repo root."""

import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT", "")
MODEL = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4.1-mini")
# Optional: the Azure OpenAI endpoint of the Foundry resource, used by the evaluators in Lab 6.
# When empty it is derived from PROJECT_ENDPOINT.
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")

PACKET_DIR = ROOT / "data" / "packet"
POLICY_PDF = ROOT / "data" / "policy" / "vendor_onboarding_policy.pdf"
GOLDEN = ROOT / "data" / "golden" / "decision_record.json"
OUT_DIR = ROOT / "out"

# The date the vendor is due to start. Every date rule in the policy is measured from it.
ONBOARDING_DATE = "2026-11-02"


def require_endpoint() -> None:
    if not PROJECT_ENDPOINT or "<" in PROJECT_ENDPOINT:
        raise SystemExit("PROJECT_ENDPOINT is missing: copy .env.example to .env and fill it in.")
    endpoint = urlparse(PROJECT_ENDPOINT)
    if (endpoint.scheme != "https" or not endpoint.netloc
            or not endpoint.path.startswith("/api/projects/")
            or not endpoint.path.removeprefix("/api/projects/").strip("/")):
        raise SystemExit("PROJECT_ENDPOINT must be https://<resource>.services.ai.azure.com/api/projects/<project>")
    if not MODEL.strip():
        raise SystemExit("MODEL_DEPLOYMENT_NAME is missing in .env.")


def evaluator_endpoint() -> str:
    """Azure OpenAI endpoint of the Foundry resource (strip /api/projects/<name>)."""
    if AZURE_OPENAI_ENDPOINT:
        return AZURE_OPENAI_ENDPOINT
    return PROJECT_ENDPOINT.split("/api/projects/")[0]
