# Lab 1: One agent, local tools

October 2026 workshop.


**Goal:** produce the onboarding decision with the simplest agent that could work.
**Technique:** one Agent Framework agent, three function tools that parse PDFs locally with
PyMuPDF, and `DecisionRecord` as structured output.

## Steps

1. **TODO 1a, 1b** in `start/onboarding_agent.py`: implement `list_documents` and `read_document`.
   Tools return text, never raise, and cannot leave the packet folder (`shared/pdf.safe_path`).
   Checkpoint: `python -c "from shared.pdf import document_text; print(document_text('02_dpa.pdf'))"`.
2. **TODO 2**: create the `Agent` with the three tools and run it with
   `options={"response_format": DecisionRecord}`.
3. Run `python labs/lab1_single_agent/start/onboarding_agent.py`, then `python score.py out/lab1.json`.

## What to look for

- R8 (signatory) should come back `unknown`: the company profile is a scanned image and
  `read_document` returns no text for it. That is the correct behaviour, and the reason for Lab 2.
- Check R1 and R2 against the decoys (72 h data-subject deadline, September vulnerability scan).
- `max_invocations` on each tool is a harness limit: the agent cannot loop on a tool forever.

## Stretch

- Remove the "Never guess" line from the instructions and rerun. Does R8 turn into a confident
  `pass`? Compare the scores.
- Ask for the decision without `response_format` and parse the text yourself. Count the failures.
