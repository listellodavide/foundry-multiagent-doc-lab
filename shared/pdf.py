"""PDF helpers built on PyMuPDF. Every file access goes through safe_path()."""

from pathlib import Path
from typing import cast

import pymupdf as fitz  # PyMuPDF

from shared.config import PACKET_DIR, POLICY_PDF


def safe_path(file: str) -> Path:
    """Resolve a file name inside the packet (or the policy PDF). Anything else is refused."""
    name = Path(file).name
    if name == POLICY_PDF.name:
        return POLICY_PDF
    path = (PACKET_DIR / name).resolve()
    if path.parent != PACKET_DIR.resolve() or not path.exists():
        raise FileNotFoundError(f"{file} is not a document in the onboarding packet")
    return path


def list_documents() -> list[dict]:
    docs = []
    for pdf in sorted(PACKET_DIR.glob("*.pdf")):
        with fitz.open(pdf) as doc:
            text_chars = sum(len(cast(str, doc[i].get_text("text")).strip()) for i in range(doc.page_count))
            docs.append({"file": pdf.name, "pages": doc.page_count, "has_text_layer": text_chars > 20})
    return docs


def page_text(file: str, page: int) -> str:
    with fitz.open(safe_path(file)) as doc:
        if not 1 <= page <= doc.page_count:
            raise ValueError(f"{file} has {doc.page_count} page(s)")
        text = cast(str, doc[page - 1].get_text("text")).strip()
    return text or "[no text layer on this page: it is a scanned image, use a vision or OCR tool]"


def document_text(file: str, max_chars: int = 12000) -> str:
    """Whole document with page markers, cut at max_chars with an explicit note."""
    path = safe_path(file)
    parts, used = [], 0
    with fitz.open(path) as doc:
        for i in range(1, doc.page_count + 1):
            text = page_text(path.name, i)
            if used + len(text) > max_chars:
                parts.append(f"[{doc.page_count - i + 1} more page(s) not shown]")
                break
            parts.append(f"--- {path.name} p{i} ---\n{text}")
            used += len(text)
    return "\n".join(parts)


def render_page_png(file: str, page: int = 1, dpi: int = 150) -> bytes:
    with fitz.open(safe_path(file)) as doc:
        if not 1 <= page <= doc.page_count:
            raise ValueError(f"{file} has {doc.page_count} page(s)")
        return doc[page - 1].get_pixmap(dpi=dpi).tobytes("png")


def source_text(source: str) -> str:
    """Text for a finding's source such as '02_dpa.pdf p1' (whole document if no page)."""
    parts = source.replace(",", " ").split()
    file = next((p for p in parts if p.endswith(".pdf")), None)
    page = next((int(p[1:]) for p in parts if p.startswith("p") and p[1:].isdigit()), None)
    if not file:
        return ""
    try:
        return page_text(file, page) if page else document_text(file)
    except (FileNotFoundError, ValueError):
        return ""


def search_text(query: str, max_hits: int = 8) -> list[dict]:
    """Case-insensitive keyword search across the packet, returning page references and a snippet."""
    words = [w.lower() for w in query.split() if len(w) > 2]
    hits = []
    for doc in list_documents():
        with fitz.open(PACKET_DIR / doc["file"]) as pdf:
            for i in range(1, pdf.page_count + 1):
                text = cast(str, pdf[i - 1].get_text("text"))
                low = text.lower()
                score = sum(low.count(w) for w in words)
                if score:
                    pos = min((low.find(w) for w in words if w in low), default=0)
                    snippet = " ".join(text[max(0, pos - 120): pos + 240].split())
                    hits.append({"source": f"{doc['file']} p{i}", "score": score, "snippet": snippet})
    return sorted(hits, key=lambda h: -h["score"])[:max_hits]
