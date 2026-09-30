# October 2026 workshop readiness

Validated on September 30, 2026 with Windows PowerShell and Python 3.14.5 in `.venv`.
This report separates code verification, successful service calls, and remaining Azure prerequisites.

## Code verification

The offline pytest suite covers policy rules and edge cases, scoring, PDF parsing/rendering,
configuration, solution/starter imports, generated starters, mocked model calls, Lab 2 indexing
failure and cleanup, planner reflection, both workflow graph branches, MCP tools, handoff history,
groundedness, variance, and tracing wiring. These tests incur no Azure costs.
Ruff and Pyright are also run against project code, including tests.
Final checks: **126 pytest tests passed with 100% statement and branch coverage**, Ruff passed,
Pyright reported **0 errors and 0 warnings**, all Python files parsed, all 18 lab scripts imported,
and `pip check` found no broken requirements.
The verified installed versions are captured in `requirements.lock.txt`.

Corrections made during verification:

- Removed unused E402 suppressions; retained the imports that still require them after bootstrap.
- Kept handoff history persistence enabled using explicit named arguments.
- Added explicit optional-value handling, valid page checks and vision refusal handling.
- Corrected the policy date window to use a calendar year and reject future dates.
- Pinned compatible MCP/FastMCP versions and installed the separate orchestration integration.
- Excluded the scanned profile from File Search and used vision for that document.
- Added Lab 2 timeout/file-failure detection and cleanup of partial uploads.
- Skipped groundedness scoring against the scanned page's no-text-layer placeholder.
- Updated all workshop edition references to October 2026. Historical scenario dates remain intact.

## Live Azure results

Project: `fdy-ai103-dlistello/ai103-lab`. Deployment: `gpt-4o-mini`, backed by `gpt-4.1-mini`.
The endpoint and deployment were inspected using Azure's management APIs. Configuration is in
the ignored `.env`; no API key is required.

| Check | Result |
| --- | --- |
| Setup: model, structured vision, Agent Service | Passed |
| Lab 1 solution | Completed; score 76.2/100 |
| Lab 2 solution | Completed; score 83.8/100; six indexed files; temporary agent/store/files cleaned up |
| Lab 3 solution | Completed; score 100/100 |
| Lab 4 solution | Completed; score 100/100 |
| Lab 5 solution | Blocked by Azure token rate limit on repeated attempts, including an isolated attempt |
| Lab 6 groundedness evaluator | Completed against Lab 4 output |
| Lab 6 variance | Covered by offline tests; repeated live runs not completed |
| Lab 6 tracing | Blocked: project has no Application Insights connection |

Model scoring measures accuracy separately from runtime success. Lab 1 missed three rule
verdicts and two scanned-profile fields. Lab 2 extracted the facts correctly but missed R4
and returned the wrong overall decision. Labs 3 and 4 judged the facts in code and matched
the golden answer. This variation is part of the workshop comparison, not a passing accuracy
guarantee for all model outputs.

## Remaining preparation

The deployment permits 10,000 tokens and 10 requests per minute. Increase its available
capacity or use a dedicated workshop deployment with sufficient quota for participant
concurrency, then rerun Lab 5 and the variance exercise. Waiting between top-level lab runs
was insufficient for the handoff workflow's internal calls.

Create or select an Application Insights resource and connect it to the project using
Foundry's tracing setup. No existing Application Insights resource was found in
`rg-ai103-dlistello`. Then rerun the tracing solution and verify the trace appears in the portal.

The project is therefore locally validated and connected to Foundry, but the complete live
workshop is not yet fully verified. See [setup instructions](workshop-setup.md) and
[test instructions](../pytest/README.md).
