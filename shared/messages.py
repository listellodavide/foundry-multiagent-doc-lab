"""Messages that flow between the Lab 4 workflow executors.

They live in an importable module (not in the lab script) so the workflow's checkpoints can
pickle them and a run can be resumed from another process.
"""

from dataclasses import dataclass, field


@dataclass
class Packet:
    texts: dict[str, str]


@dataclass
class Partial:
    source: str
    facts: dict = field(default_factory=dict)
    vendor: dict | None = None
