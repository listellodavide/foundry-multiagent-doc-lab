"""Lab 2 extension - short-term and inspectable long-term memory."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from score import load
from shared import config
from shared.clients import save_run, timed
from shared.memory import ConversationMemory, SQLiteVectorMemory


def approved_summary(record) -> str:
    failed = ", ".join(f.rule_id for f in record.findings if f.status == "fail") or "none"
    return f"Vendor {record.vendor.legal_name}; decision {record.decision}; failed rules {failed}."


def remember_and_recall(source: Path, tenant: str, session: str, query: str):
    # >>> TODO 1: keep recent turns in memory and persist only the approved summary
    _, _, record = load(str(source))
    recent = ConversationMemory(limit=4)
    recent.add("user", "Review the vendor packet")
    recent.add("assistant", approved_summary(record))
    store = SQLiteVectorMemory(config.OUT_DIR / "workshop-memory.sqlite3")
    store.add(tenant, session, approved_summary(record), {"source": source.name})
    hits = store.search(tenant, session, query, limit=2)
    return record, recent.context(), hits
    # <<< TODO 1


def main() -> None:
    source = config.OUT_DIR / "lab2.json"
    if not source.exists():
        raise SystemExit("Run the Lab 2 hosted solution first: out/lab2.json is missing")
    with timed() as timing:
        record, recent, hits = remember_and_recall(source, "contoso", "workshop", "failed vendor rules")
    print(f"Short-term turns: {len(recent)}; long-term hits: {[round(hit.score, 3) for hit in hits]}")
    save_run("lab2_memory", "2b. Short- and long-term memory", timing["seconds"], record)


if __name__ == "__main__":
    main()
