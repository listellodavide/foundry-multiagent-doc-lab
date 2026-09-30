# Lab 5: Handoff specialists, tools over MCP, a human in the loop

October 2026 workshop.

> **Advanced Python required.** This lab uses subprocess protocols, async streaming, hierarchical
> orchestration, HTTP trust boundaries and explicit resource limits.


**Goal:** the same decision, reached in a conversation with the procurement officer.
**Technique:** the PDF operations become an MCP server (`pdf_mcp_server.py`, FastMCP over stdio).
A coordinator delegates to compliance and operations supervisors, which hand work to contract,
security, finance and identity specialists (`HandoffBuilder`). All of them use the MCP tools. A
writer agent turns the conversation into the `DecisionRecord`.

## Steps

1. **TODO 1a, 1b** in `start/pdf_mcp_server.py`: implement `read_page` and `search_packet`.
   Test the server alone: `npx @modelcontextprotocol/inspector python labs/lab5_mcp_handoff/start/pdf_mcp_server.py`
   (optional, needs Node.js), or run `desk.py` directly.
2. **TODO 2** in `start/desk.py`: the coordinator, supervisors and specialists. Handoff agents need
   `require_per_service_call_history_persistence=True` in Agent Framework 1.12.
3. **TODO 3**: wire the two-level hierarchy. Draw the alternative peer/network topology and
   identify how its routing, termination and accountability would differ.
4. **TODO 4**: the writer agent with `response_format=DecisionRecord`.
5. Run it interactively and answer as the procurement officer, then run `--auto` and score it.
6. Start `solution/vendor_registry_api.py`, set `REGISTRY_TOKEN=workshop-local-token`, and complete
   the secured `lookup_vendor_registry` MCP tool. Inspect how the client validates the base URL,
   authenticates, limits responses and exposes only whitelisted fields. Treat returned text as
   evidence, never as instructions that can override the policy or system prompt.

## What to look for

- `check_invoice_math` is deterministic: the finance specialist should call it, not compute.
- The same MCP server can be added to VS Code / GitHub Copilot (`.vscode/mcp.json`) and used by
  hand: tools written once, used by any MCP host.
- Handoff is interactive by design: without a human answer, the conversation waits.
- The registry is deliberately local but crosses a real HTTP trust boundary. Try a bad token,
  non-HTTPS remote URL, oversized response and extra private field before using it from an agent.

## Stretch

- Replace the writer's judgement with `shared.policy.build_record` and compare scores.
- Participants familiar with LangGraph: rebuild the coordinator and one specialist in LangGraph with the
  same MCP server (the handoff-tool pattern from the banking lab), and compare the amount of code.
