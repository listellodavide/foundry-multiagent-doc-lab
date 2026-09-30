"""A bounded Plan-Act-Observe loop with typed, allowlisted actions."""

from collections.abc import Awaitable, Callable
from typing import Any, Literal

from pydantic import BaseModel, Field


class ReActAction(BaseModel):
    action: Literal[
        "list_documents", "read_document", "search_packet", "read_scanned_profile",
        "recall_memory", "finish",
    ]
    arguments: dict[str, Any] = Field(default_factory=dict)
    rationale_summary: str = Field(description="Brief operational reason, never hidden chain-of-thought")
    final: dict[str, Any] | None = None


class Observation(BaseModel):
    step: int
    action: str
    content: str


async def run_react(
    goal: str,
    choose: Callable[[str, list[Observation]], Awaitable[ReActAction]],
    tools: dict[str, Callable[..., Any]],
    max_steps: int = 8,
) -> tuple[dict[str, Any], list[Observation]]:
    """Run until `finish`, rejecting unknown actions and unbounded loops."""
    if max_steps < 1:
        raise ValueError("max_steps must be positive")
    observations: list[Observation] = []
    for step in range(1, max_steps + 1):
        decision = await choose(goal, observations)
        if decision.action == "finish":
            if decision.final is None:
                raise ValueError("finish requires a final payload")
            return decision.final, observations
        tool = tools.get(decision.action)
        if tool is None:
            raise ValueError(f"Action is not registered: {decision.action}")
        try:
            value = tool(**decision.arguments)
            if hasattr(value, "__await__"):
                value = await value
            content = str(value)
        except Exception as exc:  # Tool failures become observations so the agent can recover.
            content = f"ERROR: {type(exc).__name__}: {exc}"
        observations.append(Observation(step=step, action=decision.action, content=content))
    raise RuntimeError(f"ReAct loop exceeded {max_steps} steps")
