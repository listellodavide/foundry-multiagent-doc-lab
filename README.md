# Microsoft Foundry Multi-Agent 2-Day Workshop — October 2026

One business goal for the whole workshop: **decide whether Contoso Creative can onboard a new
vendor, Carpathia Localization SRL, from its 6-PDF onboarding packet.** Every lab reaches that
same decision with a different agentic technique, writes the same `DecisionRecord`, and is scored
by the same `score.py` against the same golden answer. The leaderboard at the end shows where each
technique wins, where it fails, and what it costs.

| Lab | Technique | Foundry / framework features | Time |
| --- | --- | --- | --- |
| 1 | Single agent + local PDF tools | Agent Framework `Agent`, `@tool`, structured output, `max_invocations` | 75 min |
| 2 | Hosted agent: File Search + Code Interpreter + vision | Foundry Agent Service (`azure-ai-projects` 2.x), vector store, Responses API, image input | 90 min |
| 3 | Planner + extractor + critic, policy in code | Structured plans, reflection loop, deterministic judge | 90 min |
| 4 | Workflow graph: fan-out, fan-in, switch-case | `WorkflowBuilder`, executors, checkpoints, `WorkflowViz` | 90 min |
| 5 | Handoff specialists over MCP, with a human | FastMCP server, `MCPStdioTool`, `HandoffBuilder`, human-in-the-loop | 90 min |
| 6 | Trust: leaderboard, groundedness, variance, tracing | `azure-ai-evaluation`, OpenTelemetry to Application Insights | 75 min |

## The packet (generated, fictional)

| File | What it contains | What it tests |
| --- | --- | --- |
| `01_msa.pdf` | Master services agreement, 2 pages, signatures | Payment terms, liability cap, signatory |
| `02_dpa.pdf` | Data processing addendum | Breach notice (96 h) next to a 72 h decoy |
| `03_security_questionnaire.pdf` | Vendor answers | Pen test date vs a newer vulnerability scan decoy |
| `04_insurance_certificate.pdf` | Insurance certificate | Cyber cover vs a smaller indemnity decoy, expiry |
| `05_invoice.pdf` | Setup invoice | Total that does not add up |
| `06_company_profile_scan.pdf` | Scanned image, no text layer | Needs vision: authorised signatory, register number |

The policy (`data/policy/vendor_onboarding_policy.pdf`, and `shared/policy.py`) has eight rules,
R1 to R8. The golden answer is `data/golden/decision_record.json`: decision **conditional**, with
R1, R2, R4 and R7 failing.

## Setup (once, about 10 minutes)

Prerequisites: Python 3.14 (3.12 and 3.13 also accepted), Git, Azure CLI, Zed or VS Code. No Docker, no Node.js, no Azure
Developer CLI. Azure: a Foundry project with one chat model deployment that supports vision and
structured outputs (for example `gpt-4.1-mini`), and the **Foundry User** role on the project.

```bash
git clone <this repo> && cd foundry-multiagent-doc-lab
py -3.14 -m venv .venv             # Windows; macOS/Linux: python3.14 -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env               # then fill PROJECT_ENDPOINT and MODEL_DEPLOYMENT_NAME
az login
python setup_check.py              # or --offline before you have Azure access
```

For tests and editor checks, install `requirements-dev.txt`. See
[pytest/README.md](pytest/README.md) for the offline test suite and
[workshop setup](docs/workshop-setup.md) for Windows, Zed, Azure, and troubleshooting.

## How each lab works

Each lab folder has `README.md`, `start/` (code with `TODO n` markers that raise
`NotImplementedError`) and `solution/`. Work in `start/`; compare with `solution/` when stuck.
Run everything from the repo root. After each lab:

```bash
python score.py out/lab1.json      # one run
python score.py                    # leaderboard of every run in out/
```

## Cost

Model tokens, a small vector store and Code Interpreter usage in Lab 2 (the agent, store and
uploaded files are deleted by the script). A full pass of all
six labs is a few hundred thousand tokens per participant on a mini model. Lab 6 tracing writes
to the Application Insights resource connected to the project.

## October 2026 workshop

The October 2026 workshop covers tools, agentic RAG, planning, metacognition, multi-agent
workflows, MCP, frameworks, memory, and observability through one vendor onboarding scenario
and six techniques. It uses Agent Framework 1.x and Foundry Agent Service with the Responses
API; authentication is Entra ID only. The fictional vendor's onboarding date is November 2,
2026, which is separate from the workshop date and anchors the policy checks and golden answer.

Regenerate `start/` after editing a solution: `python tools/make_start.py`.
