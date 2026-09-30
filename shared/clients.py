"""Client factories and small helpers used by all labs. Authentication is Entra ID only."""

import json
import re
import time
from contextlib import contextmanager

from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential, DefaultAzureCredential

from shared import config
from shared.schema import DecisionRecord, RunRecord


def chat_client():
    """Agent Framework chat client on the Foundry project (Responses API)."""
    from agent_framework.foundry import FoundryChatClient

    config.require_endpoint()
    return FoundryChatClient(project_endpoint=config.PROJECT_ENDPOINT, model=config.MODEL,
                             credential=AzureCliCredential())


def project_client() -> AIProjectClient:
    """Foundry project client (azure-ai-projects 2.x) for hosted agents, files, telemetry."""
    config.require_endpoint()
    return AIProjectClient(endpoint=config.PROJECT_ENDPOINT, credential=DefaultAzureCredential())


def parse_model(text: str, model):
    """Validate JSON from a model reply; tolerates ```json fences and text around the object."""
    match = re.search(r"\{.*\}", text, re.S)
    return model.model_validate_json(match.group(0) if match else text)


def response_value(response, model):
    """Structured value from an Agent Framework response, with a text fallback."""
    try:
        value = response.value
        if isinstance(value, model):
            return value
    except Exception:  # noqa: BLE001 - fall back to parsing the text
        pass
    return parse_model(response.text, model)


@contextmanager
def timed():
    box = {"start": time.perf_counter()}
    yield box
    box["seconds"] = round(time.perf_counter() - box["start"], 1)


def save_run(lab: str, technique: str, seconds: float, record: DecisionRecord) -> str:
    config.OUT_DIR.mkdir(exist_ok=True)
    path = config.OUT_DIR / f"{lab}.json"
    path.write_text(RunRecord(technique=technique, runtime_s=seconds, record=record).model_dump_json(indent=2))
    fails = [f.rule_id for f in record.findings if f.status == "fail"]
    unknown = [f.rule_id for f in record.findings if f.status == "unknown"]
    print(f"\nDecision: {record.decision.upper()}  failed: {fails}  unknown: {unknown}")
    print(f"Saved {path.relative_to(config.ROOT)} in {seconds}s. Score it with: python score.py {path.relative_to(config.ROOT)}")
    return str(path)


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1)
