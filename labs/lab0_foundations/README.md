# Lab 0: From a traditional pipeline to an agentic system

October 2026 workshop. **Time:** 40 minutes.

**Python level: Easy.** You should be able to run scripts, read functions and edit short TODO blocks.

**Goal:** recognise when an agent is useful and build the smallest bounded agent loop that still
produces the workshop's `DecisionRecord`.

## Steps

1. Run `classify_workload()` for the examples in `solution/foundations.py`. Discuss why stable
   rules and known inputs favour deterministic code while uncertain document navigation favours
   a bounded agent.
2. **TODO 1:** complete `components()` so the architecture explicitly names its goal, model,
   tools, state, guardrails, evaluator and human authority.
3. **TODO 2:** create the agent with only the packet-search tools, structured output and a clear
   stop condition. Run and score it like every other lab.

The production shape used by the later labs is hybrid: models locate and extract uncertain facts;
code validates schemas, enforces limits, applies policy and decides when a human must intervene.
