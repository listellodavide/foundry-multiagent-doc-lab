# Lab 3: Plan, extract, critique, judge in code

**Goal:** the same decision, with fewer confident mistakes.
**Technique:** a planner maps each rule to fields and documents, an extractor fills `KeyFacts`,
a critic checks every fact against its source and sends wrong ones back (at most two rounds), and
`shared.policy.build_record` applies the rules in code.

## Steps

1. **TODO 1** in `start/plan_reflect.py`: planner agent with `response_format=Plan`. Note that
   `planned_files()` filters the plan against real files: a plan is model output, not truth.
2. **TODO 2**: extractor agent with `response_format=KeyFacts`, reading only the planned files,
   with the critic's feedback appended on later rounds.
3. **TODO 3**: critic agent returning `Critique` (correct / wrong / not in source per field).
4. **TODO 4**: the loop: extract, critique, re-extract with feedback, stop when nothing is wrong or
   after `MAX_ROUNDS`.
5. Run it and score it. Compare facts accuracy and runtime with Labs 1 and 2.

## What to look for

- Which facts the critic corrected, and in which round. The decoys are designed for this.
- Rules and the decision are computed in code: dates, amounts and the decision rule cannot be
  "reasoned" wrong. Only the facts can be wrong.
- The price: count the model calls. Reflection is not free.

## Stretch

- Set `MAX_ROUNDS = 0` and measure what the critic was worth on this packet.
- Give the critic a different (larger) model deployment than the extractor.
