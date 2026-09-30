import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from score import load, score
from shared import config, pdf, vision
from shared.clients import parse_model, response_value, save_run
from shared.schema import DecisionRecord


def test_score_and_roundtrip(golden, tmp_path, monkeypatch):
    assert score(golden, golden)["total"] == 100.0
    monkeypatch.setattr(config, "OUT_DIR", tmp_path)
    monkeypatch.setattr(config, "ROOT", tmp_path)
    path = save_run("test", "unit test", 1.25, golden)
    technique, seconds, record = load(path)
    assert (technique, seconds, record) == ("unit test", 1.25, golden)


def test_scoring_reports_missing_rules_and_wrong_decision(golden):
    record = golden.model_copy(update={"findings": golden.findings[:-1], "decision": "reject"})
    result = score(record, golden)
    assert result["missed_rules"] == ["R8:missing"]
    assert not result["decision"]
    assert result["total"] < 100


def test_json_fences_and_response_fallback(golden):
    text = f"Here is the answer:\n```json\n{golden.model_dump_json()}\n```"
    assert parse_model(text, DecisionRecord) == golden
    assert response_value(SimpleNamespace(value=golden), DecisionRecord) == golden
    assert response_value(SimpleNamespace(text=text), DecisionRecord) == golden
    with pytest.raises(ValueError):
        parse_model("no JSON here", DecisionRecord)


def test_pdf_packet():
    docs = pdf.list_documents()
    assert len(docs) == 6
    assert [d["file"] for d in docs if not d["has_text_layer"]] == ["06_company_profile_scan.pdf"]
    assert "no text layer" in pdf.page_text("06_company_profile_scan.pdf", 1)
    assert pdf.render_page_png("06_company_profile_scan.pdf").startswith(b"\x89PNG")
    assert "02_dpa.pdf p1" in pdf.document_text("02_dpa.pdf")
    assert pdf.search_text("breach")
    assert pdf.source_text("02_dpa.pdf p1")
    assert pdf.source_text("missing.pdf p1") == ""
    assert pdf.source_text("no citation") == ""


@pytest.mark.parametrize("page", [0, -1, 999])
def test_invalid_pages(page):
    with pytest.raises(ValueError):
        pdf.page_text("01_msa.pdf", page)
    with pytest.raises(ValueError):
        pdf.render_page_png("01_msa.pdf", page)


def test_missing_pdf_and_truncation():
    with pytest.raises(FileNotFoundError):
        pdf.safe_path("missing.pdf")
    assert "more page(s) not shown" in pdf.document_text("01_msa.pdf", max_chars=1)


@pytest.mark.parametrize("endpoint", ["", "https://<resource>.services.ai.azure.com/api/projects/<project>",
                                      "http://example.com/api/projects/test", "https://example.com/wrong"])
def test_invalid_configuration(endpoint, monkeypatch):
    monkeypatch.setattr(config, "PROJECT_ENDPOINT", endpoint)
    with pytest.raises(SystemExit):
        config.require_endpoint()


def test_evaluator_endpoint(monkeypatch):
    monkeypatch.setattr(config, "PROJECT_ENDPOINT", "https://test.services.ai.azure.com/api/projects/workshop")
    monkeypatch.setattr(config, "AZURE_OPENAI_ENDPOINT", "")
    assert config.evaluator_endpoint() == "https://test.services.ai.azure.com"
    monkeypatch.setattr(config, "AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
    assert config.evaluator_endpoint() == "https://test.openai.azure.com"


def test_vision_refusal_is_explicit(monkeypatch):
    project = MagicMock()
    project.__enter__.return_value = project
    client = project.get_openai_client.return_value.__enter__.return_value
    client.responses.parse.return_value = SimpleNamespace(output_parsed=None)
    monkeypatch.setattr(vision, "project_client", lambda: project)
    with pytest.raises(ValueError, match="no structured profile"):
        vision.extract_profile_from_scan()


def test_golden_is_valid_json(golden):
    assert json.loads(golden.model_dump_json())["decision"] == "conditional"
