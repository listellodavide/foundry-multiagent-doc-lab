# Lab 4: A workflow graph

October 2026 workshop.

> **Advanced Python required.** This lab uses concurrent graph execution, typed messages,
> conditional routing and persistent checkpoints.


**Goal:** the same decision, with the order of work decided by a graph, not by a model.
**Technique:** Agent Framework workflow. `intake` fans out to four executors in parallel
(contract, security, finance specialists and a vision reader), `aggregator` fans in and applies the
policy in code, and a switch-case edge sends records with `unknown` rules to a `rechecker` before
the output. Checkpoints are written to `out/checkpoints/`.

## Steps

1. **TODO 1** in `start/workflow.py`: the `Specialist` executor's handler: run its agent on its own
   documents only and send a `Partial` with only its fields.
2. **TODO 2**: the `aggregator`: merge partial facts and the vendor profile, call `build_record`.
3. **TODO 3**: wire the graph with `add_fan_out_edges`, `add_fan_in_edges` and
   `add_switch_case_edge_group` (`Case` for unknown findings, `Default` to `finalize`).
4. Run it. Open `out/lab4_workflow.mmd` in a Mermaid viewer (VS Code preview or mermaid.live).
5. Score it and compare runtime with Lab 3: the specialists run in parallel.

## What to look for

- Each specialist sees one to three documents, not six: smaller context, fewer look-alike traps.
- The switch-case only fires when something is unknown. Force it by removing a document from a
  specialist's list.
- The graph is testable without a model: replace the agents with fakes and assert the routing.

## Stretch

- Add a human approval step before `finalize` with `ctx.request_info(...)`.
- Resume a run from a checkpoint in `out/checkpoints/` (`workflow.run(checkpoint_id=...)`).
