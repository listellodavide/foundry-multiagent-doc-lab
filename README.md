# Microsoft Foundry Multi-Agent Systems Workshop

## Course assignment

This repository contains the practical assignment for a three-day workshop on agent-based
application development with Microsoft Foundry. The workshop takes place in October 2026 and uses
Python 3.14.

You will implement several solutions to the same document-review problem. Each solution must
produce the same typed output, allowing you to compare correctness, runtime, reliability and
operational complexity across agent patterns and frameworks.

## Learning outcomes

By the end of the workshop, you should be able to:

1. Explain when an agentic design is appropriate and when deterministic code is preferable.
2. Build agents that call local functions, Foundry-hosted tools and MCP tools.
3. Implement ReAct, reflection, supervisor, handoff, hierarchical and graph-based patterns.
4. Distinguish short-term conversation context from persistent long-term memory.
5. Add human approval, bounded execution and deterministic policy enforcement.
6. Compare Agent Framework, LangGraph, Semantic Kernel and AutoGen using one problem and output contract.
7. Implement replay-safe orchestration with Azure Durable Functions.
8. Evaluate agent output for factual accuracy, groundedness, variance and operational risk.

## Required Python background

The workshop is intended for Python developers and cloud engineers.

> **Advanced Python requirement:** Labs 3, 4, 5, 7 and 8 require confident use of `asyncio`, type
> annotations, Pydantic models, decorators, context managers, dependency isolation and exception
> handling. Students who do not yet have this background should complete the Easy and Intermediate
> exercises first and use the supplied starter code during the Advanced labs.

| Level | Expected knowledge |
| --- | --- |
| Easy | Run scripts, read functions, edit small TODO blocks and inspect JSON |
| Intermediate | Use async calls, SDK clients, decorators, exceptions and typed models |
| Advanced | Design concurrency, orchestration, state, security boundaries and recovery behavior |

## Case study

Contoso Creative is considering Carpathia Localization SRL as a new vendor. Your program must review
a six-document onboarding packet and apply eight procurement rules, R1 through R8.

The packet contains deliberate ambiguities:

- similar deadlines with different legal meanings;
- a penetration test and a newer vulnerability scan;
- different insurance values;
- an invoice with incorrect arithmetic;
- a scanned company profile without a text layer.

Every implementation must return the `DecisionRecord` defined in `shared/schema.py`. The reference
decision is `conditional`; R1, R2, R4 and R7 fail. Do not copy the reference answer into a solution.
Your implementation must derive its result from the supplied documents and policy.

The fictional onboarding date is November 2, 2026. It is scenario input for date calculations and
is separate from the October 2026 workshop date.

## Lab programme

| Day | Lab | Assignment | Python level | Time |
| --- | --- | --- | --- | --- |
| 1 | 0 | Identify agentic components and build a bounded hybrid review | Easy | 40 min |
| 1 | 1 | Implement a single agent with local function tools | Intermediate | 75 min |
| 1 | 2 | Create a hosted Foundry agent and add short- and long-term memory | Intermediate | 105 min |
| 1 | 3 | Compare ReAct, plan-first execution and reflection | Advanced | 105 min |
| 2 | 4 | Build a parallel workflow graph with routing and checkpoints | Advanced | 90 min |
| 2 | 5 | Build hierarchical handoffs over secured MCP with human oversight | Advanced | 135 min |
| 2 | 6 | Measure accuracy, groundedness, variance and traces | Intermediate | 75 min |
| 3 | 7 | Implement and compare LangGraph, Semantic Kernel and AutoGen | Advanced | 195 min |
| 3 | 8 | Implement a recoverable workflow with Azure Durable Functions | Advanced | 135 min |

Each lab contains:

- `README.md`: assignment instructions and review questions;
- `start/`: incomplete student code containing numbered TODOs;
- `solution/`: a complete reference implementation.

Complete the files under `start/`. Use the reference solution only after attempting the exercise or
when directed by the instructor.

## Assessment and required evidence

For each completed lab, submit or retain:

1. the completed starter code;
2. the generated JSON result under `out/`;
3. the score reported by `score.py`;
4. a short explanation of one failure mode and its mitigation;
5. for Labs 4, 5, 7 and 8, a diagram or trace showing the orchestration path.

Solutions are evaluated on:

| Criterion | Weight |
| --- | ---: |
| Extracted facts | 40% |
| Policy-rule verdicts | 50% |
| Final decision | 10% |

Automated score is necessary but not sufficient. A high-scoring implementation that leaks secrets,
ignores missing evidence, loops without a bound, or cannot recover from failure does not satisfy the
assignment.

## Prerequisites

Days 1 and 2 require:

- Python 3.14;
- Git;
- Azure CLI;
- Zed or Visual Studio Code;
- a Microsoft Foundry project;
- a chat-model deployment supporting image input and structured output;
- Foundry access through Microsoft Entra ID.

Day 3 also requires:

- Azure Functions Core Tools v4;
- Azurite;
- disk space for four isolated environments under `.venvs/`.

Docker and Node.js are not required when Core Tools and Azurite are installed through native
packages or editor extensions.

## Environment setup

Run all commands from the repository root.

### Windows PowerShell

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
az login
.\.venv\Scripts\python.exe setup_check.py
```

### macOS or Linux

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
cp .env.example .env
az login
.venv/bin/python setup_check.py
```

Configure `.env` with your assigned project and deployment:

```dotenv
PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
MODEL_DEPLOYMENT_NAME=<deployment-name>
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
ENABLE_SENSITIVE_DATA=false
```

Authentication uses Entra ID. Do not place API keys, access tokens or connection strings in source
files or commits.

Prepare Day 3 separately:

```powershell
.\setup-extension-envs.bat
.\.venv\Scripts\python.exe setup_extension_check.py --offline
```

```bash
chmod +x setup-extension-envs.sh run-extension-tests.sh
./setup-extension-envs.sh
.venv/bin/python setup_extension_check.py --offline
```

Start Azurite and repeat the readiness check without `--offline` before Lab 8.

## Running and scoring an exercise

Example for Lab 1 on Windows:

```powershell
.\.venv\Scripts\python.exe labs\lab1_single_agent\start\onboarding_agent.py
.\.venv\Scripts\python.exe score.py out\lab1.json
```

Display the leaderboard for all completed runs:

```powershell
.\.venv\Scripts\python.exe score.py
```

Equivalent macOS/Linux commands use `.venv/bin/python` and forward slashes.

## Automated validation

Windows:

```powershell
.\run-all-test.bat
.\run-extension-tests.bat
```

macOS or Linux:

```bash
./run-all-test.sh
./run-extension-tests.sh
```

The base suite runs offline. It generates an isolated packet, replaces live model clients with test
doubles and does not consume Azure quota. Passing unit tests does not prove that live Azure
authentication, quota or model behavior is correct; run the assigned solution scripts as well.

## Repository structure

| Path | Contents |
| --- | --- |
| `labs/` | Assignments, starter code and reference solutions |
| `shared/` | Schemas, policy, memory, PDF, configuration and client utilities |
| `data/` | Packet generator, generated PDFs, policy and reference answer |
| `pytest/` | Offline automated tests |
| `tools/` | Starter generation and offline verification |
| `infra/durable/` | Optional Azure deployment for Lab 8 |
| `out/` | Generated results, checkpoints and reports |

## Resource use and cleanup

Live exercises consume model tokens. Lab 2 also creates uploaded files, a vector store, an agent
version and a Code Interpreter session. The reference solution deletes these resources after both
successful and failed runs. Lab 6 may send traces to Application Insights. Lab 8 runs locally by
default; Azure deployment is optional.

Delete workshop resources when instructed by the instructor. Do not reuse shared workshop resources
for production or confidential data.

Additional setup, editor and quota guidance is available in
[`docs/workshop-setup.md`](docs/workshop-setup.md). Detailed testing instructions are in
[`pytest/README.md`](pytest/README.md).
