"""Scores one or more lab outputs against the golden decision record.

    python score.py out/lab1.json
    python score.py out/*.json          # leaderboard across techniques

Score = 40% key facts + 50% rule verdicts + 10% decision. Facts compare normalised values
(dates as ISO, numbers within 0.01, names case-insensitive).
"""

import json
import sys
from pathlib import Path

from shared.config import GOLDEN
from shared.schema import DecisionRecord, RunRecord


def norm(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    return " ".join(str(value).lower().replace(",", "").split())


def score(record: DecisionRecord, golden: DecisionRecord) -> dict:
    g_facts = {**golden.facts.model_dump(), **{f"vendor.{k}": v for k, v in golden.vendor.model_dump().items()}}
    r_facts = {**record.facts.model_dump(), **{f"vendor.{k}": v for k, v in record.vendor.model_dump().items()}}
    fact_hits = {k: norm(r_facts.get(k)) == norm(v) for k, v in g_facts.items()}

    g_rules = {f.rule_id: f.status for f in golden.findings}
    r_rules = {f.rule_id: f.status for f in record.findings}
    rule_hits = {k: r_rules.get(k) == v for k, v in g_rules.items()}

    facts_acc = sum(fact_hits.values()) / len(fact_hits)
    rules_acc = sum(rule_hits.values()) / len(rule_hits)
    decision_ok = record.decision == golden.decision
    return {
        "facts": facts_acc, "rules": rules_acc, "decision": decision_ok,
        "total": round(100 * (0.4 * facts_acc + 0.5 * rules_acc + 0.1 * decision_ok), 1),
        "missed_facts": [k for k, ok in fact_hits.items() if not ok],
        "missed_rules": [f"{k}:{r_rules.get(k, 'missing')}" for k, ok in rule_hits.items() if not ok],
    }


def load(path: str) -> tuple[str, float, DecisionRecord]:
    data = json.loads(Path(path).read_text())
    if "record" in data:
        run = RunRecord.model_validate(data)
        return run.technique, run.runtime_s, run.record
    return Path(path).stem, 0.0, DecisionRecord.model_validate(data)


def main(paths: list[str]) -> None:
    golden = DecisionRecord.model_validate_json(GOLDEN.read_text())
    rows = []
    for path in paths:
        technique, seconds, record = load(path)
        rows.append((Path(path).stem, technique, seconds, score(record, golden)))
    rows.sort(key=lambda r: -r[3]["total"])
    print(f"{'run':16} {'technique':40} {'facts':>6} {'rules':>6} {'decision':>9} {'score':>6} {'time s':>7}")
    for name, technique, seconds, s in rows:
        print(f"{name[:16]:16} {technique[:40]:40} {s['facts']:6.0%} {s['rules']:6.0%} "
              f"{'ok' if s['decision'] else 'wrong':>9} {s['total']:6.1f} {seconds:7.1f}")
    for name, _, _, s in rows:
        if s["missed_facts"] or s["missed_rules"]:
            print(f"  {name}: missed facts {s['missed_facts']}  wrong rules {s['missed_rules']}")


if __name__ == "__main__":
    main(sys.argv[1:] or sorted(str(p) for p in Path("out").glob("*.json")))
