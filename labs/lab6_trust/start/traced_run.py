"""Lab 6 (part 3) - Traces in Application Insights and the Foundry portal.

Sends OpenTelemetry spans for every agent call, tool call and workflow step of the Lab 4
workflow to the Application Insights resource connected to the Foundry project.
Prerequisite: Application Insights connected to the project (Foundry portal, tracing page).

Run from the repo root:  python labs/lab6_trust/solution/traced_run.py
"""

import asyncio
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from agent_framework.observability import enable_instrumentation  # noqa: E402
from azure.monitor.opentelemetry import configure_azure_monitor  # noqa: E402
from opentelemetry import trace  # noqa: E402

from shared.clients import project_client  # noqa: E402


async def main() -> None:
    # TODO 1: send telemetry to the project's Application Insights and turn on agent instrumentation
    raise NotImplementedError("TODO 1: see the lab README")

    spec = importlib.util.spec_from_file_location("workflow", ROOT / "labs/lab4_workflow/solution/workflow.py")
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load Lab 4 workflow module")
    workflow_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = workflow_module
    spec.loader.exec_module(workflow_module)

    tracer = trace.get_tracer("onboarding-desk")
    with tracer.start_as_current_span("onboarding-review") as span:
        span.set_attribute("vendor", "Carpathia Localization SRL")
        result = await workflow_module.build_workflow().run(str(ROOT / "data/packet"))
        record = result.get_outputs()[-1]
        span.set_attribute("decision", record.decision)
    print(f"Decision {record.decision}. Open the Foundry portal > Tracing (or Application Insights > "
          "Transaction search) and find the 'onboarding-review' span; it can take 2-3 minutes to appear.")


if __name__ == "__main__":
    asyncio.run(main())
