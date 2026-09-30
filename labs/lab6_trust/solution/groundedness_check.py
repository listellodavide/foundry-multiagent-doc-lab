"""Lab 6 (part 1) - Is every finding supported by the page it cites?

Two checks per finding, cheapest first:
  1. deterministic: do the numbers and key words in the evidence appear in the cited source?
  2. LLM judge: azure-ai-evaluation GroundednessEvaluator scores the evidence against the source (1-5).
A finding that fails both is a hallucination candidate, whatever its verdict.

Run from the repo root:  python labs/lab6_trust/solution/groundedness_check.py out/lab1.json
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from azure.ai.evaluation import AzureOpenAIModelConfiguration, GroundednessEvaluator  # noqa: E402

from score import load  # noqa: E402
from shared import config  # noqa: E402
from shared.pdf import source_text  # noqa: E402
from shared.policy import RULES  # noqa: E402


def cheap_check(evidence: str, source: str) -> bool:
    """Every number in the evidence must appear in the source (formatting-insensitive)."""
    digits = lambda s: re.sub(r"[^0-9]", " ", s).split()  # noqa: E731
    source_numbers = set(digits(source))
    return all(n in source_numbers for n in digits(evidence))


def main(path: str) -> None:
    technique, _, record = load(path)
    # >>> TODO 1: configure the judge model (Entra ID, no key) and the groundedness evaluator
    judge = GroundednessEvaluator(AzureOpenAIModelConfiguration(
        azure_endpoint=config.evaluator_endpoint(), azure_deployment=config.MODEL, api_version="2024-10-21"))
    # <<< TODO 1
    print(f"{technique}\n{'rule':5} {'verdict':8} {'numbers':8} {'judge':6} source")
    suspects = 0
    for f in record.findings:
        context = source_text(f.source)
        if not context or f.status == "unknown":
            print(f"{f.rule_id:5} {f.status:8} {'-':8} {'-':6} {f.source or 'no source'}")
            continue
        # >>> TODO 2: run both checks and count findings that fail both
        numbers_ok = cheap_check(f.evidence, context)
        result = judge(query=RULES[f.rule_id][0], response=f"{f.status}: {f.evidence}", context=context)
        score = result.get("groundedness", 0)
        if not numbers_ok and score < 3:
            suspects += 1
        # <<< TODO 2
        print(f"{f.rule_id:5} {f.status:8} {'ok' if numbers_ok else 'MISSING':8} {score:<6} {f.source}")
    print(f"\n{suspects} finding(s) fail both checks: treat them as hallucinated evidence.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out/lab1.json")
