# Lab 2: Hosted agent with File Search, Code Interpreter and vision

October 2026 workshop.


**Goal:** the same decision, with the agent and its tools running in Foundry Agent Service.
**Technique:** upload the packet to a vector store, give a prompt agent File Search and Code
Interpreter, read the scanned page with a vision call, and invoke the agent through the Responses
API (`agent_reference`).

## Steps

1. **TODO 1** in `start/hosted_desk.py`: upload the five text PDFs and the policy with
   `files.create(purpose="assistants")`, create a vector store, wait until it is `completed`.
2. **TODO 2**: call `shared.vision.extract_profile_from_scan()`: the page is rendered to PNG and
   sent as `input_image`, with `VendorProfile` as the output schema.
3. **TODO 3**: `project.agents.create_version(...)` with `FileSearchTool` and `CodeInterpreterTool`.
4. **TODO 4**: `openai_client.responses.create(..., extra_body={"agent_reference": ...})`, parse the
   JSON, score it. The script uses cleanup contexts to delete the agent version, vector store
   and files, including resources created before an upload or indexing failure. Each run uses
   a unique agent name. The scanned profile goes to vision rather than the vector store.
5. Open the Foundry portal while it runs: the agent version and its tool calls are visible there.

## What to look for

- R8 should now pass: vision read the scanned profile that File Search cannot index.
- File Search citations name the file but not the page. Lab 6's groundedness check falls back to
  the whole document, which is weaker evidence than a page reference.
- R7: did the agent use Code Interpreter for the arithmetic? Check the response output items.

## Stretch

- Remove the vision step. Does the hosted agent say `unknown` for R8, or guess?
- Build the same agent in the Foundry portal playground with the same files and compare answers.
