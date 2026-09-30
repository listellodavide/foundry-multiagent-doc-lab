"""Positive and negative tests for the workshop readiness checker."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import setup_check
from shared import clients, config, pdf, vision


def configure_local_checks(monkeypatch, *, docs=6, score="100.0"):
    monkeypatch.setattr(setup_check.sys, "version_info", (3, 14))
    monkeypatch.setattr(setup_check.importlib, "import_module", MagicMock())
    runs = [SimpleNamespace(stdout="", stderr=""), SimpleNamespace(stdout=score, stderr="detail")]
    monkeypatch.setattr(setup_check.subprocess, "run", MagicMock(side_effect=runs))
    monkeypatch.setattr(pdf, "list_documents", lambda: [{}] * docs)


def test_setup_offline_success(monkeypatch, capsys):
    configure_local_checks(monkeypatch)
    monkeypatch.setattr(setup_check, "OFFLINE", True)
    with pytest.raises(SystemExit) as stopped:
        setup_check.main()
    assert stopped.value.code == 0
    assert "Offline checks passed" in capsys.readouterr().out


def test_setup_rejects_python_version(monkeypatch, capsys):
    monkeypatch.setattr(setup_check.sys, "version_info", (3, 11))
    with pytest.raises(SystemExit) as stopped:
        setup_check.main()
    assert stopped.value.code == 1
    assert "use 3.12, 3.13 or 3.14" in capsys.readouterr().out


def test_setup_reports_missing_package(monkeypatch, capsys):
    monkeypatch.setattr(setup_check.sys, "version_info", (3, 14))
    monkeypatch.setattr(setup_check.importlib, "import_module", MagicMock(side_effect=ImportError("missing")))
    with pytest.raises(SystemExit) as stopped:
        setup_check.main()
    assert stopped.value.code == 1
    assert "cannot import" in capsys.readouterr().out


@pytest.mark.parametrize("docs,score,message", [(5, "100.0", "expected 6"), (6, "99.9", "scorer self-test")])
def test_setup_rejects_bad_local_assets(monkeypatch, capsys, docs, score, message):
    configure_local_checks(monkeypatch, docs=docs, score=score)
    monkeypatch.setattr(setup_check, "OFFLINE", True)
    with pytest.raises(SystemExit) as stopped:
        setup_check.main()
    assert stopped.value.code == 1
    assert message in capsys.readouterr().out


def test_setup_online_success(monkeypatch, golden, capsys):
    configure_local_checks(monkeypatch)
    monkeypatch.setattr(setup_check, "OFFLINE", False)
    monkeypatch.setattr(config, "require_endpoint", MagicMock())

    class FakeAgent:
        def __init__(self, **kwargs):
            pass

        run = AsyncMock(return_value=SimpleNamespace(text="READY"))

    import agent_framework

    monkeypatch.setattr(agent_framework, "Agent", FakeAgent)
    monkeypatch.setattr(clients, "chat_client", lambda: object())
    monkeypatch.setattr(vision, "extract_profile_from_scan", lambda: golden.vendor)
    project = MagicMock()
    project.__enter__.return_value = project
    project.agents.list.return_value = [object()]
    monkeypatch.setattr(clients, "project_client", lambda: project)
    setup_check.main()
    output = capsys.readouterr().out
    assert "Agent Framework -> Foundry: READY" in output
    assert "All checks passed" in output


def test_setup_wraps_azure_failure(monkeypatch, capsys):
    configure_local_checks(monkeypatch)
    monkeypatch.setattr(setup_check, "OFFLINE", False)
    monkeypatch.setattr(config, "require_endpoint", MagicMock())

    class BrokenAgent:
        def __init__(self, **kwargs):
            pass

        run = AsyncMock(side_effect=RuntimeError("quota"))

    import agent_framework

    monkeypatch.setattr(agent_framework, "Agent", BrokenAgent)
    monkeypatch.setattr(clients, "chat_client", lambda: object())
    with pytest.raises(SystemExit) as stopped:
        setup_check.main()
    assert stopped.value.code == 1
    assert "Azure call failed (RuntimeError)" in capsys.readouterr().out
