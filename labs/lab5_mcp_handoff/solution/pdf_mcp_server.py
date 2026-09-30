"""Lab 5 (part 1) - The packet as an MCP server.

Exposes the PDF operations as Model Context Protocol tools, so any MCP host can use them:
the Agent Framework agents in desk.py, VS Code / GitHub Copilot, the MCP Inspector, or a
LangGraph agent. The server runs over stdio; the host starts it as a child process.

Try it on its own:  npx @modelcontextprotocol/inspector python labs/lab5_mcp_handoff/solution/pdf_mcp_server.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from fastmcp import FastMCP  # noqa: E402

from shared import pdf  # noqa: E402
from shared.policy import policy_text  # noqa: E402

mcp = FastMCP(name="pdf-desk")


# Read-only PDF operations exposed as MCP tools.
@mcp.tool()
def list_documents() -> str:
    """List the onboarding packet PDFs with page counts and whether each has a text layer."""
    return json.dumps(pdf.list_documents())


@mcp.tool()
def read_page(file: str, page: int = 1) -> str:
    """Return the text of one page. Cite it as '<file> p<page>'."""
    # >>> TODO 1a: return pdf.page_text(file, page); return 'ERROR: ...' instead of raising
    try:
        return pdf.page_text(file, page)
    except (FileNotFoundError, ValueError) as e:
        return f"ERROR: {e}"
    # <<< TODO 1a


@mcp.tool()
def search_packet(query: str) -> str:
    """Keyword search across the packet; returns page references and snippets, best match first."""
    # >>> TODO 1b: return the hits of pdf.search_text(query) as JSON
    return json.dumps(pdf.search_text(query))
    # <<< TODO 1b


@mcp.tool()
def read_policy() -> str:
    """The vendor onboarding policy: rules R1 to R8, onboarding date and decision rule."""
    return policy_text()


@mcp.tool()
def check_invoice_math(subtotal: float, vat: float, total: float) -> str:
    """Deterministic check that subtotal + VAT equals the total, to the cent."""
    expected = round(subtotal + vat, 2)
    ok = abs(expected - total) < 0.01
    return json.dumps({"ok": ok, "expected_total": expected, "stated_total": total,
                       "difference": round(total - expected, 2)})


@mcp.tool()
def read_scanned_profile(file: str = "06_company_profile_scan.pdf") -> str:
    """Read a scanned (image-only) page with a vision model and return the vendor profile as JSON."""
    from shared.vision import extract_profile_from_scan  # needs az login and the Foundry project
    return extract_profile_from_scan(file).model_dump_json()


if __name__ == "__main__":
    mcp.run(show_banner=False)  # stdio; the banner would corrupt the protocol stream
