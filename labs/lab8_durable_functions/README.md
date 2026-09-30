# Lab 8: Reliable agent workflows with Azure Durable Functions

October 2026 workshop. **Time:** 135 minutes. Advanced extension-day lab.

> **Advanced Python required.** You should understand generators, replay-safe orchestration,
> idempotent activities, asynchronous HTTP workflows and external-event handling.

Prerequisites: Python 3.14, Azure Functions Core Tools v4 and Azurite. Copy
`local.settings.example.json` to `local.settings.json`, start Azurite, then run `func start` from
the solution or starter directory.

The HTTP starter creates a durable instance. The orchestrator fans out four activities, retries
transient activity failures, fans in a deterministic `DecisionRecord`, and waits for a human
approval external event with a durable timer. Orchestrator code performs no network, filesystem,
clock or random operations, so replay remains deterministic. Activities own all side effects and
persist results idempotently by instance ID.

Run `python run_local.py` in a second terminal to start, inspect, approve and score the review.
Restart the Functions host while the instance is waiting to demonstrate recovery from storage.
Azure deployment is optional and must use managed identity and a Python 3.14-compatible hosting
plan such as Flex Consumption.
