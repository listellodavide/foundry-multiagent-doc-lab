# October 2026 workshop setup

## Python and Windows

Python 3.14 is selected in `.python-version`. Create and use the environment from the
repository root:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe setup_check.py --offline
.\.venv\Scripts\python.exe -m pytest -q
```

For the coverage report, run:

```powershell
.\.venv\Scripts\coverage.exe run -m pytest -q
.\.venv\Scripts\coverage.exe report
```

See [the unit-test guide](../pytest/README.md) for focused tests, failure diagnostics and HTML coverage.

`requirements.lock.txt` captures the complete installed package versions from this validation,
including development tools. Use `pip install -r requirements.lock.txt` to reproduce that
environment for the workshop rather than resolving newer transitive dependencies.

Calling the environment's Python directly also works when PowerShell blocks activation.
The focused Agent Framework packages include core, Foundry, OpenAI transport and orchestrations.
MCP and FastMCP are pinned to compatible versions because MCP 2.x renamed APIs used by the
framework version in this workshop. Dependency installation and evaluator imports were
verified on Python 3.14.5; the old Python 3.14/PyRIT restriction was obsolete for this installation.

## Zed warnings and imports

Open the whole repository, use `toolchain: select`, and select `.venv`. Zed configures its
Python language server from that toolchain. The repository also includes `pyrightconfig.json`
and `ruff.toml`. See [Zed's Python documentation](https://zed.dev/docs/languages/python).

`# noqa: E402` suppresses the lint warning for a module-level import following executable code.
Scripts launched by file path add the repository root to `sys.path` before importing `shared`.
Keep the suppression where that bootstrap still triggers E402. Unneeded E402 suppressions were
removed from other imports. `setup_check.py` now places its delayed imports inside `main()`.
A `noqa` comment affects linting only; it cannot fix missing packages or type-checker errors.

Starter imports and assignments are deliberately unused or absent until participants complete
the TODOs. Ruff has narrowly scoped exceptions for F401, F821 and F841 in `labs/*/start/*.py`.
Solutions receive all configured checks. Pyright runs in basic mode with explicit Python 3.14
and local import paths. Passing `require_per_service_call_history_persistence=True` directly
to each handoff agent preserves behavior and avoids ambiguous `**dict[str, bool]` arguments.

## Foundry connection

Copy `.env.example` to `.env` and set the project's actual endpoint and deployment name:

```dotenv
PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
MODEL_DEPLOYMENT_NAME=<deployment-name>
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
ENABLE_SENSITIVE_DATA=false
```

Use the deployment name, which can differ from the underlying model name. The existing lab
resource checked during preparation has deployment `gpt-4o-mini` backed by `gpt-4.1-mini`.
Each participant should configure their own project/deployment as applicable. `.env` is ignored
by Git. Authentication uses Entra ID rather than API keys.

```powershell
az login
.\.venv\Scripts\python.exe setup_check.py
```

The account needs the appropriate project role (Foundry User for agent use) and model access.
The setup check verifies a model response, structured vision and Agent Service access.
See [Microsoft's Foundry SDK quickstart](https://learn.microsoft.com/en-us/azure/foundry/quickstarts/get-started-code).

For Lab 6, connect Application Insights to the project through the Foundry portal's tracing
setup before running `traced_run.py`. The project's telemetry connection is separate from
the model connection. A missing connection does not prevent Labs 1–5 from running.

## Capacity and live checks

The inspected deployment allows 10,000 tokens and 10 requests per minute. That is a small
shared quota for agent handoffs and classroom concurrency. Run live checks sequentially,
allow the quota window to reset after throttling, and size deployment capacity in Foundry
before the workshop. Unit tests cannot validate Azure quota or service availability.
Lab 5 caps coordinator and specialist replies at 1,024 tokens and the writer at 4,096 tokens;
these limits reduce response reservations but do not remove the deployment's token quota.

Lab 2 indexes the five text documents plus the policy. The image-only profile is processed
with vision. Indexing timeout/failure triggers cleanup of partially uploaded resources.
The solution creates a unique agent version for each run and deletes its temporary resources.
Code Interpreter incurs charges in addition to model tokens; see
[Microsoft's Code Interpreter documentation](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/code-interpreter).

Run `solution/` scripts to validate completed implementations. `start/` scripts intentionally
raise `NotImplementedError` until the exercises are completed. Successful execution does not
guarantee the model's answer is correct: compare each output against the golden answer with
`python score.py`. Labs 3 and 4 apply the policy in code; Labs 1 and 2 also ask the model to judge it.

The workshop takes place in October 2026. The fictional vendor starts on November 2, 2026;
the packet's historical dates and policy reference date are scenario data, not workshop dates.
