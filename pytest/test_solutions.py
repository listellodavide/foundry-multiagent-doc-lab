import ast
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from shared import config
from shared.messages import Packet
from shared.schema import DecisionRecord
from tools.make_start import strip
from tools.verify_offline import load_module


@pytest.mark.parametrize("path", sorted(config.ROOT.glob("labs/*/*/*.py")), ids=lambda p: str(p.relative_to(config.ROOT)))
def test_all_lab_scripts_import(path):
    load_module(path)


@pytest.mark.parametrize("path", sorted(config.ROOT.glob("labs/*/solution/*.py")), ids=lambda p: p.name)
def test_starters_match_solutions(path):
    starter = path.parent.parent / "start" / path.name
    expected = ast.dump(ast.parse(strip(path.read_text(encoding="utf-8"))))
    actual = ast.dump(ast.parse(starter.read_text(encoding="utf-8")))
    assert actual == expected


async def test_lab1_agent_structured_result(solution, golden, monkeypatch):
    lab = solution("lab1_single_agent/solution/onboarding_agent.py")
    agent = MagicMock()
    agent.run = AsyncMock(return_value=SimpleNamespace(value=golden))
    factory = MagicMock(return_value=agent)
    monkeypatch.setattr(lab, "Agent", factory)
    monkeypatch.setattr(lab, "chat_client", lambda: object())
    assert await lab.run() == golden
    assert agent.run.await_args.kwargs["options"]["response_format"] is DecisionRecord
    assert len(factory.call_args.kwargs["tools"]) == 3


def test_lab1_document_errors_return_text(solution):
    lab = solution("lab1_single_agent/solution/onboarding_agent.py")
    assert lab.read_document.func("missing.pdf").startswith("ERROR:")


@pytest.mark.parametrize("mode", ["success", "failed", "expired", "timeout", "partial-upload", "file-failed"])
def test_lab2_upload_and_cleanup(solution, monkeypatch, mode):
    lab = solution("lab2_foundry_hosted/solution/hosted_desk.py")
    client = MagicMock()
    client.files.create.side_effect = [SimpleNamespace(id=f"file-{i}") for i in range(6)]
    if mode == "partial-upload":
        client.files.create.side_effect = [SimpleNamespace(id="file-0"), RuntimeError("upload failed")]
    client.vector_stores.create.return_value = SimpleNamespace(id="store")
    status = {"success": "completed", "file-failed": "completed", "failed": "failed",
              "expired": "expired", "timeout": "in_progress", "partial-upload": "completed"}[mode]
    client.vector_stores.retrieve.return_value = SimpleNamespace(
        status=status, file_counts=SimpleNamespace(failed=int(mode == "file-failed")))
    monkeypatch.setattr(lab.time, "sleep", lambda _: None)
    if mode == "success":
        files, store = lab.upload_packet(client)
        assert len(files) == 6 and store == "store"
        client.files.delete.assert_not_called()
        client.vector_stores.delete.assert_not_called()
    else:
        with pytest.raises((RuntimeError, TimeoutError)):
            lab.upload_packet(client)
        assert client.files.delete.call_count == (1 if mode == "partial-upload" else 6)
        assert client.vector_stores.delete.call_count == (0 if mode == "partial-upload" else 1)


@pytest.mark.parametrize("fail_response", [False, True])
def test_lab2_main_cleans_resources(solution, golden, monkeypatch, fail_response):
    lab = solution("lab2_foundry_hosted/solution/hosted_desk.py")
    project = MagicMock()
    project.__enter__.return_value = project
    client = project.get_openai_client.return_value.__enter__.return_value
    project.agents.create_version.return_value = SimpleNamespace(name="test-agent", version="1")
    client.responses.create.return_value = SimpleNamespace(output_text=golden.model_dump_json())
    if fail_response:
        client.responses.create.side_effect = RuntimeError("model failed")
    monkeypatch.setattr(lab, "project_client", lambda: project)
    monkeypatch.setattr(lab, "upload_packet", lambda _: (["file-a", "file-b"], "store"))
    monkeypatch.setattr(lab, "extract_profile_from_scan", lambda: golden.vendor)
    save = MagicMock()
    monkeypatch.setattr(lab, "save_run", save)
    if fail_response:
        with pytest.raises(RuntimeError, match="model failed"):
            lab.main()
        save.assert_not_called()
    else:
        lab.main()
        assert save.call_args.args[-1] == golden
    project.agents.delete_version.assert_called_once_with(agent_name="test-agent", agent_version="1")
    client.vector_stores.delete.assert_called_once_with(vector_store_id="store")
    assert client.files.delete.call_count == 2


def test_lab3_planner_output_is_filtered(solution):
    lab = solution("lab3_plan_reflect/solution/plan_reflect.py")
    step = lab.PlanStep(rule_id="R1", fact_fields=["breach_notification_hours"],
                        documents=["02_dpa.pdf", "invented.pdf", "06_company_profile_scan.pdf"], what_to_look_for="breach")
    assert lab.planned_files(lab.Plan(steps=[step])) == ["02_dpa.pdf"]
    assert len(lab.planned_files(lab.Plan(steps=[]))) == 5


async def test_lab3_reflects_then_stops(solution, golden, monkeypatch):
    lab = solution("lab3_plan_reflect/solution/plan_reflect.py")
    monkeypatch.setattr(lab, "chat_client", lambda: object())
    monkeypatch.setattr(lab, "make_plan", AsyncMock(return_value=lab.Plan(steps=[])))
    extract = AsyncMock(return_value=golden.facts)
    monkeypatch.setattr(lab, "extract_facts", extract)
    wrong = lab.FactCheck(field="breach_notification_hours", verdict="wrong", correct_value="96", reason="DPA")
    critic = AsyncMock(side_effect=[lab.Critique(checks=[wrong]), lab.Critique(checks=[])])
    monkeypatch.setattr(lab, "critique", critic)
    monkeypatch.setattr(lab, "extract_profile_from_scan", lambda: golden.vendor)
    saved = MagicMock()
    monkeypatch.setattr(lab, "save_run", saved)
    await lab.main()
    assert extract.await_count == 2
    assert critic.await_count == 2
    assert extract.await_args is not None
    assert "96" in extract.await_args.args[2]
    assert saved.call_args.args[-1].decision == golden.decision


async def test_lab4_specialist_limits_fact_fields(solution, golden):
    lab = solution("lab4_workflow/solution/workflow.py")
    agent = MagicMock()
    agent.run = AsyncMock(return_value=SimpleNamespace(value=golden.facts))
    specialist = lab.Specialist(agent, ["01_msa.pdf"], ["payment_terms_days"], id="test")
    context = SimpleNamespace(send_message=AsyncMock())
    await specialist.extract(Packet(texts={"01_msa.pdf": "MSA", "05_invoice.pdf": "PRIVATE"}), context)
    partial = context.send_message.await_args.args[0]
    assert partial.facts == {"payment_terms_days": golden.facts.payment_terms_days}
    assert "PRIVATE" not in agent.run.await_args.args[0]


async def test_lab4_rechecker_only_merges_missing_fields(solution, golden):
    lab = solution("lab4_workflow/solution/workflow.py")
    facts = golden.facts.model_copy(update={"payment_terms_days": None})
    initial = lab.build_record(facts, golden.vendor)
    response = golden.facts.model_copy(update={"invoice_total": 99999})
    agent = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(value=response)))
    context = SimpleNamespace(yield_output=AsyncMock())
    await lab.Rechecker(agent).recheck(initial, context)
    record = context.yield_output.await_args.args[0]
    assert record.facts.payment_terms_days == golden.facts.payment_terms_days
    assert record.facts.invoice_total == golden.facts.invoice_total


@pytest.mark.parametrize("needs_recheck", [False, True])
async def test_lab4_complete_graph_offline(solution, golden, monkeypatch, tmp_path, needs_recheck):
    lab = solution("lab4_workflow/solution/workflow.py")
    monkeypatch.setattr(lab, "chat_client", lambda: object())
    agents = {}

    def fact_agent(client, name):
        facts = golden.facts
        if name == "contract" and needs_recheck:
            facts = facts.model_copy(update={"payment_terms_days": None})
        agent = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(value=facts)))
        agents[name] = agent
        return agent

    monkeypatch.setattr(lab, "fact_agent", fact_agent)
    monkeypatch.setattr(lab, "extract_profile_from_scan", lambda: golden.vendor)
    monkeypatch.setattr(config, "OUT_DIR", tmp_path)
    workflow = lab.build_workflow()
    result = await workflow.run(str(config.PACKET_DIR))
    record = result.get_outputs()[-1]
    assert {f.rule_id: f.status for f in record.findings} == {f.rule_id: f.status for f in golden.findings}
    assert record.decision == golden.decision
    assert agents["rechecker"].run.await_count == int(needs_recheck)
    assert (tmp_path / "checkpoints").exists()


def test_lab5_pdf_tools(solution):
    lab = solution("lab5_mcp_handoff/solution/pdf_mcp_server.py")
    assert lab.read_page("missing.pdf").startswith("ERROR:")
    assert lab.read_page("01_msa.pdf", 0).startswith("ERROR:")
    assert len(json.loads(lab.list_documents())) == 6
    assert json.loads(lab.search_packet("breach"))
    assert json.loads(lab.check_invoice_math(100, 20, 120))["ok"]
    wrong = json.loads(lab.check_invoice_math(100, 20, 121))
    assert not wrong["ok"] and wrong["difference"] == 1


def test_lab5_agents_keep_handoff_history(solution, monkeypatch):
    lab = solution("lab5_mcp_handoff/solution/desk.py")
    factory = MagicMock(side_effect=lambda **kwargs: SimpleNamespace(name=kwargs["name"]))
    builder = MagicMock()
    builder.with_start_agent.return_value = builder
    builder.add_handoff.return_value = builder
    monkeypatch.setattr(lab, "Agent", factory)
    monkeypatch.setattr(lab, "HandoffBuilder", lambda **kwargs: builder)
    lab.build_desk(object(), object())
    assert factory.call_count == 7
    assert all(call.kwargs["require_per_service_call_history_persistence"] for call in factory.call_args_list)
    assert builder.add_handoff.call_count == 9


def test_lab6_groundedness_numbers(solution):
    lab = solution("lab6_trust/solution/groundedness_check.py")
    assert lab.cheap_check("notify within 96 hours", "Notification: 96 hours")
    assert not lab.cheap_check("notify within 72 hours", "Notification: 96 hours")


async def test_lab6_repeat_reports_variance(solution, golden, monkeypatch, capsys):
    lab = solution("lab6_trust/solution/repeat.py")
    run = AsyncMock(return_value=golden)
    monkeypatch.setattr(lab, "one_run", run)
    await lab.main("lab1", 2)
    assert run.await_count == 2
    assert "mean 100.0" in capsys.readouterr().out


@pytest.mark.parametrize("lab_name,runs", [("lab1", 0), ("lab1", -1), ("missing", 2)])
async def test_lab6_repeat_invalid_arguments(solution, lab_name, runs):
    lab = solution("lab6_trust/solution/repeat.py")
    with pytest.raises(ValueError):
        await lab.main(lab_name, runs)


async def test_lab6_tracing_wires_project_and_workflow(solution, golden, monkeypatch):
    lab = solution("lab6_trust/solution/traced_run.py")
    project = MagicMock()
    project.__enter__.return_value = project
    project.telemetry.get_application_insights_connection_string.return_value = "InstrumentationKey=test"
    monkeypatch.setattr(lab, "project_client", lambda: project)
    configure = MagicMock()
    instrument = MagicMock()
    monkeypatch.setattr(lab, "configure_azure_monitor", configure)
    monkeypatch.setattr(lab, "enable_instrumentation", instrument)
    monkeypatch.setenv("ENABLE_SENSITIVE_DATA", "false")
    tracer = MagicMock()
    monkeypatch.setattr(lab.trace, "get_tracer", lambda _: tracer)
    workflow = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(get_outputs=lambda: [golden])))
    loader = MagicMock()
    loader.exec_module.side_effect = lambda module: setattr(module, "build_workflow", lambda: workflow)
    real_spec = lab.importlib.util.spec_from_file_location
    monkeypatch.setattr(lab.importlib.util, "spec_from_file_location", lambda name, path: real_spec(name, path, loader=loader))
    await lab.main()
    configure.assert_called_once_with(connection_string="InstrumentationKey=test")
    instrument.assert_called_once_with(enable_sensitive_data=False)
    workflow.run.assert_awaited_once()
    tracer.start_as_current_span.assert_called_once_with("onboarding-review")


async def test_mcp_server_discovers_tools():
    from tools.verify_offline import check_mcp
    await check_mcp(config.ROOT / "labs/lab5_mcp_handoff/solution/pdf_mcp_server.py")
