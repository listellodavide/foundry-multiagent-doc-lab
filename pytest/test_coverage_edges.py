"""Positive and negative branch tests for remaining workshop logic."""

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import score as scorer
from shared import clients, config, pdf, policy, vision
from shared.messages import Partial
from shared.schema import DecisionRecord
from tools import make_start, verify_offline


def test_client_factories_and_helpers(monkeypatch, golden):
    credential = object()
    foundry = MagicMock(return_value="chat")
    project = MagicMock(return_value="project")
    monkeypatch.setattr(config, "require_endpoint", MagicMock())
    monkeypatch.setattr("agent_framework.foundry.FoundryChatClient", foundry)
    monkeypatch.setattr(clients, "AzureCliCredential", lambda: credential)
    monkeypatch.setattr(clients, "DefaultAzureCredential", lambda: credential)
    monkeypatch.setattr(clients, "AIProjectClient", project)
    assert clients.chat_client() == "chat"
    assert clients.project_client() == "project"
    foundry.assert_called_once_with(project_endpoint=config.PROJECT_ENDPOINT, model=config.MODEL,
                                    credential=credential)
    project.assert_called_once_with(endpoint=config.PROJECT_ENDPOINT, credential=credential)

    response = SimpleNamespace(value="wrong type", text=golden.model_dump_json())
    assert clients.response_value(response, DecisionRecord) == golden
    response = SimpleNamespace(text=golden.model_dump_json())
    assert clients.response_value(response, DecisionRecord) == golden
    assert json.loads(clients.dumps({"name": "Café"}))["name"] == "Café"


def test_timed_records_elapsed_time(monkeypatch):
    ticks = iter([10.0, 11.234])
    monkeypatch.setattr(clients.time, "perf_counter", lambda: next(ticks))
    with clients.timed() as timing:
        assert timing == {"start": 10.0}
    assert timing["seconds"] == 1.2


def test_configuration_accepts_valid_and_rejects_blank_model(monkeypatch):
    monkeypatch.setattr(config, "PROJECT_ENDPOINT", "https://resource.services.ai.azure.com/api/projects/lab")
    monkeypatch.setattr(config, "MODEL", "gpt")
    config.require_endpoint()
    monkeypatch.setattr(config, "MODEL", "  ")
    with pytest.raises(SystemExit, match="MODEL_DEPLOYMENT_NAME"):
        config.require_endpoint()
    monkeypatch.setattr(config, "PROJECT_ENDPOINT", "https://resource.services.ai.azure.com/api/projects/")
    monkeypatch.setattr(config, "MODEL", "gpt")
    with pytest.raises(SystemExit, match="must be"):
        config.require_endpoint()


def test_policy_leap_year_and_custom_rationale(golden):
    assert policy._within_previous_year("2023-02-28", "2024-02-29")
    assert not policy._within_previous_year("2023-02-27", "2024-02-29")
    with pytest.raises(ValueError, match="Missing date"):
        policy._within_previous_year(None, "2024-02-29")
    record = policy.build_record(golden.facts, golden.vendor, rationale="Human-approved explanation")
    assert record.rationale == "Human-approved explanation"


def test_pdf_policy_path_and_empty_search():
    assert pdf.safe_path(config.POLICY_PDF.name) == config.POLICY_PDF
    assert pdf.search_text("a an to") == []


def test_vision_success_payload(monkeypatch, golden):
    project = MagicMock()
    project.__enter__.return_value = project
    openai = project.get_openai_client.return_value.__enter__.return_value
    openai.responses.parse.return_value = SimpleNamespace(output_parsed=golden.vendor)
    monkeypatch.setattr(vision, "project_client", lambda: project)
    monkeypatch.setattr(vision, "render_page_png", lambda file, page: b"png")
    assert vision.extract_profile_from_scan("scan.pdf", 2) == golden.vendor
    call = openai.responses.parse.call_args.kwargs
    assert call["model"] == config.MODEL
    assert call["input"][0]["content"][1]["image_url"].endswith("cG5n")


def test_score_normalization_raw_load_and_cli(golden, tmp_path, capsys):
    assert scorer.norm(None) is None
    assert scorer.norm(1.234) == 1.23
    assert scorer.norm("  A,  B ") == "a b"
    raw = tmp_path / "raw.json"
    raw.write_text(golden.model_dump_json(), encoding="utf-8")
    technique, seconds, record = scorer.load(str(raw))
    assert technique == "raw" and seconds == 0 and record == golden
    wrong = golden.model_copy(update={"decision": "reject"})
    wrapped = tmp_path / "wrapped.json"
    wrapped.write_text(json.dumps({"technique": "z", "runtime_s": 2, "record": wrong.model_dump()}), encoding="utf-8")
    scorer.main([str(wrapped), str(raw)])
    output = capsys.readouterr().out
    assert output.index("raw") < output.index("wrapped")
    assert "wrong" in output
    incomplete = golden.model_copy(update={"findings": golden.findings[:-1]})
    incomplete_path = tmp_path / "incomplete.json"
    incomplete_path.write_text(incomplete.model_dump_json(), encoding="utf-8")
    scorer.main([str(incomplete_path)])
    assert "wrong rules" in capsys.readouterr().out


async def test_lab1_tools_and_main(solution, golden, monkeypatch):
    lab = solution("lab1_single_agent/solution/onboarding_agent.py")
    assert len(json.loads(lab.list_documents.func())) == 6
    assert "R1" in lab.read_policy.func()
    monkeypatch.setattr(lab, "run", AsyncMock(return_value=golden))
    saved = MagicMock()
    monkeypatch.setattr(lab, "save_run", saved)
    await lab.main()
    saved.assert_called_once()


async def test_lab3_agent_steps_positive_and_feedback(solution, golden, monkeypatch):
    lab = solution("lab3_plan_reflect/solution/plan_reflect.py")
    plan = lab.Plan(steps=[lab.PlanStep(rule_id="R1", fact_fields=["breach_notification_hours"],
                                       documents=["02_dpa.pdf"], what_to_look_for="deadline")])
    outputs = [plan, golden.facts, golden.facts,
               lab.Critique(checks=[lab.FactCheck(field="breach_notification_hours", verdict="correct",
                                                  correct_value=None, reason="matches")])]
    agents = []

    class FakeAgent:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.run = AsyncMock(return_value=SimpleNamespace(value=outputs[len(agents)]))
            agents.append(self)

    monkeypatch.setattr(lab, "Agent", FakeAgent)
    made = await lab.make_plan(object())
    first = await lab.extract_facts(object(), plan)
    corrected = await lab.extract_facts(object(), plan, "use 96")
    review = await lab.critique(object(), plan, golden.facts)
    assert made == plan and first == golden.facts and corrected == golden.facts
    assert review.checks[0].verdict == "correct"
    assert "A reviewer found" not in agents[1].run.await_args.args[0]
    assert "use 96" in agents[2].run.await_args.args[0]
    assert agents[3].run.await_args.kwargs["options"]["response_format"] is lab.Critique


async def test_lab3_uses_maximum_correction_rounds(solution, golden, monkeypatch):
    lab = solution("lab3_plan_reflect/solution/plan_reflect.py")
    step = lab.PlanStep(rule_id="R1", fact_fields=["breach_notification_hours"],
                        documents=["02_dpa.pdf"], what_to_look_for="deadline")
    monkeypatch.setattr(lab, "chat_client", lambda: object())
    monkeypatch.setattr(lab, "make_plan", AsyncMock(return_value=lab.Plan(steps=[step])))
    extract = AsyncMock(return_value=golden.facts)
    wrong = lab.FactCheck(field="breach_notification_hours", verdict="wrong", correct_value="96", reason="DPA")
    monkeypatch.setattr(lab, "extract_facts", extract)
    monkeypatch.setattr(lab, "critique", AsyncMock(return_value=lab.Critique(checks=[wrong])))
    monkeypatch.setattr(lab, "extract_profile_from_scan", lambda: golden.vendor)
    monkeypatch.setattr(lab, "save_run", MagicMock())
    await lab.main()
    assert extract.await_count == lab.MAX_ROUNDS + 1


async def test_lab4_helpers_and_main(solution, golden, monkeypatch, tmp_path):
    lab = solution("lab4_workflow/solution/workflow.py")
    factory = MagicMock(return_value="agent")
    monkeypatch.setattr(lab, "Agent", factory)
    assert lab.fact_agent(object(), "facts") == "agent"

    send = AsyncMock()
    await getattr(lab.intake, "_original_func")(str(config.PACKET_DIR), SimpleNamespace(send_message=send))
    assert send.await_args is not None
    assert len(send.await_args.args[0].texts) == 5
    monkeypatch.setattr(lab, "extract_profile_from_scan", lambda: golden.vendor)
    send.reset_mock()
    await getattr(lab.profile_reader, "_original_func")(SimpleNamespace(), SimpleNamespace(send_message=send))
    assert send.await_args is not None
    assert send.await_args.args[0].vendor["legal_name"] == golden.vendor.legal_name
    send.reset_mock()
    parts = [Partial("facts", facts=golden.facts.model_dump()), Partial("profile", vendor=golden.vendor.model_dump())]
    await getattr(lab.aggregator, "_original_func")(parts, SimpleNamespace(send_message=send))
    assert send.await_args is not None
    assert send.await_args.args[0].decision == golden.decision
    output = AsyncMock()
    await getattr(lab.finalize, "_original_func")(golden, SimpleNamespace(yield_output=output))
    output.assert_awaited_once_with(golden)

    workflow = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(get_outputs=lambda: [golden])))
    monkeypatch.setattr(lab, "build_workflow", lambda: workflow)
    monkeypatch.setattr(lab, "WorkflowViz", lambda _: SimpleNamespace(to_mermaid=lambda: "graph"))
    monkeypatch.setattr(lab.config, "OUT_DIR", tmp_path)
    saved = MagicMock()
    monkeypatch.setattr(lab, "save_run", saved)
    await lab.main()
    assert (tmp_path / "lab4_workflow.mmd").read_text() == "graph"
    saved.assert_called_once()


def _events(items):
    async def stream():
        for item in items:
            yield item
    return stream()


async def test_lab5_conversation_auto_and_termination(solution, monkeypatch):
    lab = solution("lab5_mcp_handoff/solution/desk.py")

    class Request:
        created = []

        def __init__(self, agent_response):
            self.agent_response = agent_response

        @staticmethod
        def create_response(answer):
            Request.created.append(answer)
            return f"response:{answer}"

        @staticmethod
        def terminate():
            return "terminated"

    monkeypatch.setattr(lab, "HandoffAgentUserRequest", Request)
    messages = [SimpleNamespace(text="checked", author_name="coordinator"),
                SimpleNamespace(text="", author_name="silent")]
    requests = [SimpleNamespace(type="ignored", data=None),
                SimpleNamespace(type="request_info", request_id="one",
                                data=Request(agent_response=SimpleNamespace(messages=messages)))]
    more = [SimpleNamespace(type="request_info", request_id="two",
                            data=Request(agent_response=SimpleNamespace(messages=[])))]
    terminate = [SimpleNamespace(type="request_info", request_id="three",
                                 data=Request(agent_response=SimpleNamespace(messages=[])))]
    invalid = [SimpleNamespace(type="request_info", request_id="bad", data=object())]
    workflow = SimpleNamespace(run=MagicMock(
        side_effect=[_events(requests), _events(more), _events(terminate), _events(invalid), _events([])]))
    transcript = await lab.converse(workflow, auto=True)
    assert transcript[0].startswith("officer: We want")
    assert "coordinator: checked" in transcript
    assert transcript[-1] == "officer: terminate"
    assert Request.created == lab.AUTO_REPLIES[1:]
    assert workflow.run.call_count == 5


async def test_lab5_conversation_interactive_and_empty(solution, monkeypatch):
    lab = solution("lab5_mcp_handoff/solution/desk.py")

    class Request:
        def __init__(self, agent_response):
            self.agent_response = agent_response

        @staticmethod
        def create_response(answer):
            return answer

        @staticmethod
        def terminate():
            return "stop"

    monkeypatch.setattr(lab, "HandoffAgentUserRequest", Request)
    answers = iter(["start", "terminate"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    req = SimpleNamespace(type="request_info", request_id="r",
                          data=Request(agent_response=SimpleNamespace(messages=[])))
    workflow = SimpleNamespace(run=MagicMock(side_effect=[_events([req]), _events([])]))
    transcript = await lab.converse(workflow, auto=False)
    assert transcript == ["officer: start", "officer: terminate"]
    empty = SimpleNamespace(run=MagicMock(return_value=_events([])))
    monkeypatch.setattr("builtins.input", lambda _: "only")
    assert await lab.converse(empty, auto=False) == ["officer: only"]


async def test_lab5_conversation_harness_limit(solution, monkeypatch):
    lab = solution("lab5_mcp_handoff/solution/desk.py")

    class Request:
        pass

    monkeypatch.setattr(lab, "HandoffAgentUserRequest", Request)
    invalid = SimpleNamespace(type="request_info", request_id="ignored", data=object())
    workflow = SimpleNamespace(run=MagicMock(side_effect=lambda *args, **kwargs: _events([invalid])))
    transcript = await lab.converse(workflow, auto=True)
    assert len(transcript) == 1
    assert workflow.run.call_count == 9  # initial request plus the eight-turn harness limit


async def test_lab5_main_writes_structured_record(solution, golden, monkeypatch):
    lab = solution("lab5_mcp_handoff/solution/desk.py")

    @asynccontextmanager
    async def fake_mcp(**kwargs):
        yield "tools"

    writer = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(value=golden)))
    monkeypatch.setattr(lab, "MCPStdioTool", fake_mcp)
    monkeypatch.setattr(lab, "chat_client", lambda: "client")
    monkeypatch.setattr(lab, "build_desk", lambda client, tools: "workflow")
    monkeypatch.setattr(lab, "converse", AsyncMock(return_value=["officer: start"]))
    monkeypatch.setattr(lab, "Agent", MagicMock(return_value=writer))
    saved = MagicMock()
    monkeypatch.setattr(lab, "save_run", saved)
    await lab.main(auto=True)
    assert writer.run.await_args.kwargs["options"]["response_format"] is DecisionRecord
    saved.assert_called_once()


def test_lab5_remaining_pdf_tools(solution, golden, monkeypatch):
    lab = solution("lab5_mcp_handoff/solution/pdf_mcp_server.py")
    assert "R1" in lab.read_policy()
    monkeypatch.setattr("shared.vision.extract_profile_from_scan", lambda file: golden.vendor)
    assert json.loads(lab.read_scanned_profile())["legal_name"] == golden.vendor.legal_name


def test_lab6_groundedness_positive_negative_and_skips(solution, golden, monkeypatch, capsys):
    lab = solution("lab6_trust/solution/groundedness_check.py")
    findings = [
        golden.findings[0].model_copy(update={"source": "missing"}),
        golden.findings[1].model_copy(update={"status": "unknown"}),
        golden.findings[2].model_copy(update={"source": "scan"}),
        golden.findings[3].model_copy(update={"evidence": "EUR 999"}),
        golden.findings[4].model_copy(update={"evidence": "45 days"}),
    ]
    record = golden.model_copy(update={"findings": findings})
    monkeypatch.setattr(lab, "load", lambda path: ("technique", 0, record))
    contexts = {"missing": "", "scan": "[no text layer on this page: scanned]"}
    monkeypatch.setattr(lab, "source_text", lambda source: contexts.get(source, "source contains 45"))
    judge = MagicMock(side_effect=[{"groundedness": "2"}, {"groundedness": 5}])
    monkeypatch.setattr(lab, "GroundednessEvaluator", lambda model: judge)
    monkeypatch.setattr(lab, "AzureOpenAIModelConfiguration", lambda **kwargs: kwargs)
    lab.main("result.json")
    output = capsys.readouterr().out
    assert "1 finding(s) fail both checks" in output
    assert judge.call_count == 2


async def test_lab6_one_run_both_paths_and_unstable(solution, golden, monkeypatch, capsys):
    lab = solution("lab6_trust/solution/repeat.py")
    lab1 = SimpleNamespace(run=AsyncMock(return_value=golden))
    workflow = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(get_outputs=lambda: [golden])))
    lab4 = SimpleNamespace(build_workflow=lambda: workflow)
    monkeypatch.setattr(lab, "load_module", MagicMock(side_effect=[lab1, lab4]))
    assert await lab.one_run("lab1") == golden
    assert await lab.one_run("lab4") == golden
    changed = golden.model_copy(deep=True)
    changed.findings[0].status = "pass"
    monkeypatch.setattr(lab, "one_run", AsyncMock(side_effect=[golden, changed]))
    await lab.main("lab1", 2)
    assert "R1" in capsys.readouterr().out


def test_lab6_module_loader_success(solution, tmp_path):
    lab = solution("lab6_trust/solution/repeat.py")
    module_path = tmp_path / "loadable.py"
    module_path.write_text("answer = 42\n", encoding="utf-8")
    assert lab.load_module(module_path).answer == 42


def test_dynamic_module_load_failures(solution, monkeypatch, tmp_path):
    repeat = solution("lab6_trust/solution/repeat.py")
    traced = solution("lab6_trust/solution/traced_run.py")
    monkeypatch.setattr(repeat.importlib.util, "spec_from_file_location", lambda *args: None)
    with pytest.raises(ImportError, match="Cannot load"):
        repeat.load_module(tmp_path / "missing.py")
    project = MagicMock()
    project.__enter__.return_value = project
    project.telemetry.get_application_insights_connection_string.return_value = "connection"
    monkeypatch.setattr(traced, "project_client", lambda: project)
    monkeypatch.setattr(traced, "configure_azure_monitor", MagicMock())
    monkeypatch.setattr(traced, "enable_instrumentation", MagicMock())
    monkeypatch.setattr(traced.importlib.util, "spec_from_file_location", lambda *args: None)
    with pytest.raises(ImportError, match="Cannot load"):
        asyncio.run(traced.main())


def test_make_start_strip_and_main(tmp_path, monkeypatch):
    source = "before\n    # >>> TODO 7: implement\n    hidden\n    # <<< TODO 7\nafter\n"
    stripped = make_start.strip(source)
    assert "hidden" not in stripped and "NotImplementedError" in stripped and stripped.endswith("\n")
    root = tmp_path / "repo"
    solution = root / "labs" / "lab" / "solution"
    solution.mkdir(parents=True)
    (solution / "code.py").write_text(source, encoding="utf-8")
    (solution / "note.txt").write_text("copy", encoding="utf-8")
    (solution / "ignored-directory").mkdir()
    start = solution.parent / "start"
    start.mkdir()
    (start / "old.txt").write_text("old", encoding="utf-8")
    monkeypatch.setattr(make_start, "ROOT", root)
    make_start.main()
    assert not (start / "old.txt").exists()
    assert "NotImplementedError" in (start / "code.py").read_text(encoding="utf-8")
    assert (start / "note.txt").read_text(encoding="utf-8") == "copy"
    second = root / "labs" / "second" / "solution"
    second.mkdir(parents=True)
    (second / "code.py").write_text("value = 1\n", encoding="utf-8")
    make_start.main()
    assert (second.parent / "start" / "code.py").exists()


def test_verify_loader_and_missing_mcp_tool(monkeypatch, tmp_path):
    monkeypatch.setattr(verify_offline.importlib.util, "spec_from_file_location", lambda *args: None)
    with pytest.raises(RuntimeError, match="Cannot load"):
        verify_offline.load_module(config.ROOT / "missing.py")

    class FakeMCP:
        def __init__(self, **kwargs):
            self.functions = [SimpleNamespace(name="list_documents")]

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

    monkeypatch.setattr("agent_framework.MCPStdioTool", FakeMCP)
    with pytest.raises(AssertionError, match="Missing MCP tools"):
        asyncio.run(verify_offline.check_mcp(Path("server.py")))


def test_complete_offline_verifier(monkeypatch, capsys):
    check = AsyncMock()
    monkeypatch.setattr(verify_offline, "check_mcp", check)
    verify_offline.main()
    check.assert_awaited_once()
    assert "Offline verification passed" in capsys.readouterr().out


def test_offline_verifier_detects_page_validation_regression(monkeypatch):
    monkeypatch.setattr(verify_offline.pdf, "page_text", lambda file, page: "incorrectly accepted")
    monkeypatch.setattr(verify_offline, "check_mcp", AsyncMock())
    with pytest.raises(AssertionError, match="Page zero should be rejected"):
        verify_offline.main()


def test_packet_generator_rejects_overflow():
    generator = verify_offline.load_module(config.ROOT / "data/generate_packet.py")
    page = MagicMock()
    page.insert_textbox.return_value = -2.5
    document = MagicMock()
    document.new_page.return_value = page
    with pytest.raises(ValueError, match="overflows by 2 pt"):
        generator.write_pages(document, "Too long", ["body"])
