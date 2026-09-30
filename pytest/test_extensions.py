"""Deterministic tests for the three-day workshop extensions."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import setup_extension_check as extension_check
from shared.memory import ConversationMemory, SQLiteVectorMemory, redact, similarity, vectorize
from shared.react import ReActAction, run_react
from shared.registry import RegistryRecord, _safe_base_url, lookup_vendor
from shared.schema import KeyFacts


def test_short_and_long_term_memory_are_bounded_isolated_and_redacted(tmp_path):
    recent = ConversationMemory(2)
    recent.add("user", "one")
    recent.add("assistant", "two")
    recent.add("user", "three")
    assert recent.context() == [("assistant", "two"), ("user", "three")]
    with pytest.raises(ValueError, match="positive"):
        ConversationMemory(0)

    store = SQLiteVectorMemory(tmp_path / "memory.sqlite3")
    store.add("tenant-a", "session-a", "breach deadline 96 hours token=secret",
              {"source": "DPA"})
    store.add("tenant-a", "session-a", "invoice arithmetic failed", {"source": "invoice"})
    store.add("tenant-b", "session-a", "breach deadline 72 hours", {})
    hits = store.search("tenant-a", "session-a", "breach notification", 1)
    assert hits[0].metadata == {"source": "DPA"}
    assert "secret" not in hits[0].text
    assert store.search("tenant-b", "session-a", "breach", 5)[0].text.endswith("72 hours")
    with pytest.raises(ValueError, match="positive"):
        store.search("tenant-a", "session-a", "x", 0)
    store.clear("tenant-a", "session-a")
    assert store.search("tenant-a", "session-a", "breach") == []
    assert "IBAN" in redact("RO49AAAA1B31007593840000")
    assert similarity(vectorize("same words"), vectorize("same words")) == pytest.approx(1.0)


async def test_react_success_tool_error_and_limits():
    decisions = iter([
        ReActAction(action="read_document", arguments={"file": "x"}, rationale_summary="read"),
        ReActAction(action="finish", rationale_summary="done", final={"decision": "conditional"}),
    ])

    async def choose(goal, observations):
        assert goal == "review"
        return next(decisions)

    payload, observations = await run_react(
        "review", choose, {"read_document": lambda file: f"read {file}"}, max_steps=2)
    assert payload == {"decision": "conditional"}
    assert observations[0].content == "read x"

    async def fails(goal, observations):
        return ReActAction(action="read_document", rationale_summary="retry")

    with pytest.raises(RuntimeError, match="exceeded"):
        await run_react("review", fails, {"read_document": lambda: 1 / 0}, max_steps=1)
    with pytest.raises(ValueError, match="positive"):
        await run_react("review", fails, {}, max_steps=0)
    with pytest.raises(ValueError, match="not registered"):
        await run_react("review", fails, {}, max_steps=1)

    async def bad_finish(goal, observations):
        return ReActAction(action="finish", rationale_summary="too early")

    with pytest.raises(ValueError, match="final payload"):
        await run_react("review", bad_finish, {}, max_steps=1)


def test_foundations_and_memory_exercise(solution, golden, tmp_path, monkeypatch):
    foundations = solution("lab0_foundations/solution/foundations.py")
    assert foundations.classify_workload(True, False, False) == "deterministic"
    assert foundations.classify_workload(False, True, True) == "agentic"
    assert foundations.classify_workload(True, True, False) == "hybrid"
    assert "structured output" in foundations.components().guardrails

    memory_lab = solution("lab2_foundry_hosted/solution/memory_review.py")
    source = tmp_path / "lab2.json"
    source.write_text(json.dumps({"technique": "hosted", "runtime_s": 1,
                                  "record": golden.model_dump()}), encoding="utf-8")
    monkeypatch.setattr(memory_lab.config, "OUT_DIR", tmp_path)
    record, recent, hits = memory_lab.remember_and_recall(source, "t", "s", "failed rules")
    assert record == golden and len(recent) == 2 and hits


async def test_react_lab_uses_typed_controller(solution, golden, monkeypatch):
    lab = solution("lab3_plan_reflect/solution/react_loop.py")
    response = SimpleNamespace(value=ReActAction(action="finish", rationale_summary="complete",
                                                  final=golden.model_dump()))
    agent = SimpleNamespace(run=AsyncMock(return_value=response))
    monkeypatch.setattr(lab, "Agent", MagicMock(return_value=agent))
    action = await lab.choose(object(), "goal", [])
    assert action.action == "finish"
    assert agent.run.await_args.kwargs["options"]["response_format"] is ReActAction


def test_registry_validation_and_whitelisting(monkeypatch):
    assert _safe_base_url("http://127.0.0.1:8765") == "http://127.0.0.1:8765"
    assert _safe_base_url("https://registry.example") == "https://registry.example"
    for value in ("http://registry.example", "https://user:pass@registry.example", "file:///tmp/x"):
        with pytest.raises(ValueError):
            _safe_base_url(value)
    with pytest.raises(ValueError, match="registration"):
        lookup_vendor("", token="x")
    with pytest.raises(RuntimeError, match="TOKEN"):
        lookup_vendor("A", base_url="http://localhost:1", token="")

    class Response:
        length = 1

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, size):
            return json.dumps({"registration_number": "R", "legal_name": "Vendor", "status": "active",
                               "country": "IT", "private": "drop"}).encode()

    monkeypatch.setattr("shared.registry.urlopen", lambda request, timeout: Response())
    record = lookup_vendor("R", base_url="http://localhost:8765", token="secret")
    assert record == RegistryRecord(registration_number="R", legal_name="Vendor", status="active", country="IT")
    assert "private" not in record.model_dump()

    mcp = __import__("tools.verify_offline", fromlist=["load_module"]).load_module(
        Path(__file__).parents[1] / "labs/lab5_mcp_handoff/solution/pdf_mcp_server.py")
    monkeypatch.setattr(mcp, "lookup_vendor", lambda value: record)
    assert json.loads(mcp.lookup_vendor_registry("R"))["status"] == "active"
    monkeypatch.setattr(mcp, "lookup_vendor", MagicMock(side_effect=RuntimeError("offline")))
    assert mcp.lookup_vendor_registry("R") == "ERROR: offline"


async def test_framework_common_contract(solution, golden, monkeypatch):
    common = solution("lab7_framework_comparison/solution/common.py")
    empty = KeyFacts(**{name: None for name in KeyFacts.model_fields})
    merged = common.merge_facts([empty, golden.facts])
    assert merged == golden.facts
    monkeypatch.setattr("builtins.input", lambda _: "invalid")
    with pytest.raises(ValueError, match="approve or reject"):
        await common.approve(golden)
    assert await common.approve(golden, auto=True) == golden


def test_durable_pure_contract(solution, golden, tmp_path, monkeypatch):
    durable = solution("lab8_durable_functions/solution/function_app.py")
    monkeypatch.setattr(durable, "ROOT", tmp_path)
    parts = [golden.facts, KeyFacts(**{name: None for name in KeyFacts.model_fields}),
             KeyFacts(**{name: None for name in KeyFacts.model_fields})]
    record = durable.combine([part.model_dump() for part in parts] + [golden.vendor.model_dump()])
    assert record.facts == golden.facts and record.vendor == golden.vendor
    payload = {"instance_id": "safe-id", "record": record.model_dump()}
    first = durable.persist_activity(payload)
    second = durable.persist_activity(payload)
    assert first == second
    assert Path(first["path"]).exists()


def test_extension_setup_check_success_and_failures(tmp_path, monkeypatch, capsys):
    pythons = {}
    for name in extension_check.ENVIRONMENTS:
        executable = tmp_path / name / "python.exe"
        executable.parent.mkdir()
        executable.touch()
        pythons[name] = executable
    monkeypatch.setattr(extension_check, "environment_python", lambda name: pythons[name])
    monkeypatch.setattr(extension_check.subprocess, "run",
                        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""))
    monkeypatch.setattr(extension_check, "command_version",
                        lambda command: "4.5.0" if command == "func" else "3.33.0")
    monkeypatch.setattr(extension_check, "port_open", lambda host, port: True)
    extension_check.main()
    assert "setup passed" in capsys.readouterr().out

    pythons["langgraph"] = tmp_path / "missing"
    monkeypatch.setattr(extension_check, "command_version", lambda command: None)
    with pytest.raises(SystemExit) as stopped:
        extension_check.main(offline=True)
    message = str(stopped.value)
    assert "missing" in message and "Core Tools" in message and "Azurite" in message


def test_extension_check_helpers(monkeypatch):
    monkeypatch.setattr(extension_check.shutil, "which", lambda command: None)
    assert extension_check.command_version("missing") is None
    monkeypatch.setattr(extension_check.socket, "create_connection", MagicMock(side_effect=OSError))
    assert not extension_check.port_open("localhost", 1)
