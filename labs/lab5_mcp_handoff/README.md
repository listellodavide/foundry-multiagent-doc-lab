# Lab 5: Handoff specialists, tools over MCP, a human in the loop

October 2026 workshop.


**Goal:** the same decision, reached in a conversation with the procurement officer.
**Technique:** the PDF operations become an MCP server (`pdf_mcp_server.py`, FastMCP over stdio).
A coordinator hands the conversation to contract, security and finance specialists
(`HandoffBuilder`); all of them use the MCP tools. A writer agent turns the conversation into the
`DecisionRecord`.

## Steps

1. **TODO 1a, 1b** in `start/pdf_mcp_server.py`: implement `read_page` and `search_packet`.
   Test the server alone: `npx @modelcontextprotocol/inspector python labs/lab5_mcp_handoff/start/pdf_mcp_server.py`
   (optional, needs Node.js), or run `desk.py` directly.
2. **TODO 2** in `start/desk.py`: the coordinator and three specialists. Handoff agents need
   `require_per_service_call_history_persistence=True` in Agent Framework 1.12.
3. **TODO 3**: handoff rules: coordinator to each specialist, each specialist back to coordinator.
4. **TODO 4**: the writer agent with `response_format=DecisionRecord`.
5. Run it interactively and answer as the procurement officer, then run `--auto` and score it.

## What to look for

- `check_invoice_math` is deterministic: the finance specialist should call it, not compute.
- The same MCP server can be added to VS Code / GitHub Copilot (`.vscode/mcp.json`) and used by
  hand: tools written once, used by any MCP host.
- Handoff is interactive by design: without a human answer, the conversation waits.

## Stretch

- Replace the writer's judgement with `shared.policy.build_record` and compare scores.
- Participants familiar with LangGraph: rebuild the coordinator and one specialist in LangGraph with the
  same MCP server (the handoff-tool pattern from the banking lab), and compare the amount of code.
