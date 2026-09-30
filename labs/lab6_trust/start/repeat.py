"""Lab 6 (part 2) - Same input, same technique, different answers?

Runs one technique several times and reports the spread of scores. LLM output varies from
run to run; a technique that scores 95 once and 70 the next time is not ready for procurement.

Run from the repo root:  python labs/lab6_trust/solution/repeat.py lab1 3
                         python labs/lab6_trust/solution/repeat.py lab4 3
"""

import asyncio
import importlib.util
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from score import score  # noqa: E402
from shared.config import GOLDEN  # noqa: E402
from shared.schema import DecisionRecord  # noqa: E402

LABS = {
    "lab1": ROOT / "labs/lab1_single_agent/solution/onboarding_agent.py",
    "lab4": ROOT / "labs/lab4_workflow/solution/workflow.py",
}


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


async def one_run(lab: str) -> DecisionRecord:
    module = load_module(LABS[lab])
    if lab == "lab1":
        return await module.run()
    result = await module.build_workflow().run(str(ROOT / "data/packet"))
    return result.get_outputs()[-1]


async def main(lab: str, runs: int) -> None:
    golden = DecisionRecord.model_validate_json(GOLDEN.read_text())
    totals, verdicts = [], []
    # TODO 1: run the technique N times, score each run, and collect the rule verdicts
    raise NotImplementedError("TODO 1: see the lab README")
    spread = statistics.pstdev(totals) if len(totals) > 1 else 0.0
    unstable = sorted({r for v in verdicts for r in v if len({x.get(r) for x in verdicts}) > 1})
    print(f"\n{lab}: mean {statistics.mean(totals):.1f}, min {min(totals):.1f}, max {max(totals):.1f}, "
          f"std {spread:.1f}. Rules whose verdict changed between runs: {unstable or 'none'}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "lab1",
                     int(sys.argv[2]) if len(sys.argv) > 2 else 3))
