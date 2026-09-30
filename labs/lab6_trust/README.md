# Lab 6: Trust the result

October 2026 workshop.

**Python level: Intermediate.** This lab uses evaluators, repeated runs and telemetry configuration.


**Goal:** decide which technique you would put in front of procurement, with evidence.
**Technique:** four measurements on the outputs of Labs 1 to 5.

## Steps

1. **Leaderboard:** `python score.py` scores every run in `out/`. Facts, rule verdicts, decision,
   runtime, and what each run missed.
2. **Groundedness** (TODO 1, 2 in `start/groundedness_check.py`): for each finding, a cheap check
   (do the numbers in the evidence appear in the cited page?) and the `GroundednessEvaluator`
   from `azure-ai-evaluation` as LLM judge. Run it on the best and the worst run.
3. **Variance** (TODO 1 in `start/repeat.py`): `python labs/lab6_trust/start/repeat.py lab1 3` and
   `... lab4 3`. Same input, same code: how much does the score move between runs?
4. **Tracing** (TODO 1 in `start/traced_run.py`): send the Lab 4 workflow's spans to Application
   Insights through the Foundry project, then find the `onboarding-review` trace in the portal.

## What to look for

- A high score with ungrounded evidence is luck, not quality.
- Rules whose verdict flips between runs: those are where a human or code must decide.
- In the trace: which step takes the time, and how many tokens each agent uses.

## Debrief questions

- Which technique would you use for 50 packets a week? For one unusual contract?
- Which parts should never be done by a model in this process?
- What would you add to the golden set before trusting any of them?
