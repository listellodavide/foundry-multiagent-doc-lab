"""Import every lab and exercise local workshop behavior without Azure calls.

Run from the repository root: python -m tools.verify_offline
"""

import ast
import asyncio
import importlib.util
import sys
from pathlib import Path

from score import score
from shared import config, pdf
from shared.policy import build_record
from shared.schema import DecisionRecord, KeyFacts, VendorProfile


def load_module(path: Path):
    name = "verify_" + "_".join(path.relative_to(config.ROOT).with_suffix("").parts)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


async def check_mcp(server: Path) -> None:
    from agent_framework import MCPStdioTool

    async with MCPStdioTool(name="offline-pdf-check", command=sys.executable,
                            args=[str(server)]) as tools:
        names = {tool.name for tool in tools.functions}
        expected = {"list_documents", "read_page", "search_packet", "read_policy",
                    "check_invoice_math", "read_scanned_profile"}
        if not expected.issubset(names):
            raise AssertionError(f"Missing MCP tools: {expected - names}")
    print("[OK] MCP subprocess startup and discovery of all six tools")


def main() -> None:
    paths = sorted(p for p in config.ROOT.rglob("*.py")
                   if not any(part in {".venv", ".git", ".pytest-tmp", "__pycache__"}
                              for part in p.parts))
    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] Syntax of all {len(paths)} Python files")
    labs = sorted(config.ROOT.glob("labs/*/*/*.py"))
    for path in labs:
        load_module(path)
    print(f"[OK] Imports and decorators of all {len(labs)} solution and starter scripts")

    golden = DecisionRecord.model_validate_json(config.GOLDEN.read_text(encoding="utf-8"))
    record = build_record(golden.facts, golden.vendor)
    assert score(record, golden)["total"] == 100.0, "Code policy disagrees with golden answer"
    unknown_facts = golden.facts.model_copy(update={key: None for key in KeyFacts.model_fields})
    unknown_vendor = golden.vendor.model_copy(update={key: None for key in VendorProfile.model_fields})
    assert all(f.status == "unknown" for f in build_record(unknown_facts, unknown_vendor).findings)
    print("[OK] Policy, golden answer (100/100), and missing-fact handling")

    docs = pdf.list_documents()
    assert len(docs) == 6
    assert sum(not d["has_text_layer"] for d in docs) == 1
    for doc in docs:
        assert pdf.document_text(doc["file"])
    assert pdf.render_page_png("06_company_profile_scan.pdf").startswith(b"\x89PNG")
    assert pdf.search_text("breach")
    assert pdf.source_text("02_dpa.pdf p1")
    try:
        pdf.page_text("01_msa.pdf", 0)
    except ValueError:
        pass
    else:
        raise AssertionError("Page zero should be rejected")
    assert pdf.source_text("nonexistent.pdf p1") == ""
    print("[OK] PDF text, scanned rendering, search, citations and invalid-page handling")
    asyncio.run(check_mcp(config.ROOT / "labs/lab5_mcp_handoff/solution/pdf_mcp_server.py"))
    print("Offline verification passed. Azure workflows and exercise TODOs require separate runs.")


if __name__ == "__main__":
    main()
