"""Azure Durable Functions v2-model application for the workshop's vendor review."""

import asyncio
import json
import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "labs/lab7_framework_comparison/solution"))

from common import DOMAINS, extract_domain, merge_facts  # noqa: E402

from shared.policy import build_record  # noqa: E402
from shared.schema import DecisionRecord, KeyFacts, VendorProfile  # noqa: E402
from shared.vision import extract_profile_from_scan  # noqa: E402

try:
    import azure.durable_functions as df
    import azure.functions as func
except ModuleNotFoundError:  # Base workshop installs before extension-day dependencies.
    df = None
    func = None


def combine(parts: list[dict]) -> DecisionRecord:
    facts = merge_facts([KeyFacts.model_validate(item) for item in parts[:3]])
    profile = VendorProfile.model_validate(parts[3])
    return build_record(facts, profile)


async def extract_activity(payload: dict) -> dict:
    return (await extract_domain(payload["domain"])).model_dump()


async def profile_activity(_: dict) -> dict:
    return (await asyncio.to_thread(extract_profile_from_scan)).model_dump()


def persist_activity(payload: dict) -> dict:
    """Idempotent local sink; a deployed version replaces this with Blob Storage."""
    output = ROOT / "out" / "durable" / f"{payload['instance_id']}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload["record"], indent=2), encoding="utf-8")
    temporary.replace(output)
    return {"path": str(output), "record": payload["record"]}


if df is not None and func is not None:
    app = df.DFApp(http_auth_level=func.AuthLevel.FUNCTION)

    @app.route(route="reviews", methods=["POST"])
    @app.durable_client_input(client_name="client")
    async def start_review(req: func.HttpRequest, client):
        instance_id = await client.start_new("review_orchestrator", None, req.get_json() or {})
        return client.create_check_status_response(req, instance_id)

    @app.route(route="reviews/{instance_id}/approval", methods=["POST"])
    @app.durable_client_input(client_name="client")
    async def submit_approval(req: func.HttpRequest, client):
        value = (req.get_json() or {}).get("decision", "reject")
        if value not in {"approve", "reject"}:
            return func.HttpResponse("decision must be approve or reject", status_code=400)
        await client.raise_event(req.route_params["instance_id"], "approval", value)
        return func.HttpResponse(status_code=202)

    @app.orchestration_trigger(context_name="context")
    def review_orchestrator(context):
        # >>> TODO 1: fan out with retries, fan in, then wait for approval or a durable timeout
        retry = df.RetryOptions(first_retry_interval_in_milliseconds=1000, max_number_of_attempts=3)
        tasks = [context.call_activity_with_retry("extract_domain_activity", retry, {"domain": domain})
                 for domain in DOMAINS]
        tasks.append(context.call_activity_with_retry("extract_profile_activity", retry, {}))
        parts = yield context.task_all(tasks)
        record = yield context.call_activity("combine_activity", parts)
        approval = context.wait_for_external_event("approval")
        timeout = context.create_timer(context.current_utc_datetime + timedelta(minutes=10))
        winner = yield context.task_any([approval, timeout])
        decision = approval.result if winner == approval else "timeout"
        if winner == approval:
            timeout.cancel()
        record["human_decision"] = decision
        return (yield context.call_activity(
            "persist_result_activity",
            {"instance_id": context.instance_id, "record": record},
        ))
        # <<< TODO 1

    @app.activity_trigger(input_name="payload")
    async def extract_domain_activity(payload: dict) -> dict:
        return await extract_activity(payload)

    @app.activity_trigger(input_name="payload")
    async def extract_profile_activity(payload: dict) -> dict:
        return await profile_activity(payload)

    @app.activity_trigger(input_name="parts")
    def combine_activity(parts: list[dict]) -> dict:
        return combine(parts).model_dump()

    @app.activity_trigger(input_name="payload")
    def persist_result_activity(payload: dict) -> dict:
        return persist_activity(payload)
else:
    app = None
