
"""Read and normalize source data. Keep every physical PDF page."""

from pathlib import Path
import re
import unicodedata

from pypdf import PdfReader
from .models import DocumentPage


def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace without discarding useful structure."""

    if not text:
        return ""

    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\ufeff", "").replace("\u200b", "")

    # Normalize horizontal whitespace but preserve paragraph breaks.
    text = re.sub(r"[^\S\n]+", " ", text)

    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Keep paragraph boundaries.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _extract_fallback(path: Path, page_index: int) -> str:
    """Try PyMuPDF if pypdf extracts no text."""

    try:
        import fitz

        with fitz.open(str(path)) as pdf:
            return pdf[page_index].get_text("text") or ""

    except ImportError:
        return ""

    except Exception:
        return ""


def load_pdf(
    path: Path,
    document_id: str,
    source: str
) -> list[DocumentPage]:
    """Extract all physical pages without automatically excluding short pages."""

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    reader = PdfReader(str(path))

    if reader.is_encrypted:
        try:
            if not reader.decrypt(""):
                raise ValueError("PDF requires a password.")
        except Exception as exc:
            raise ValueError(f"Cannot open encrypted PDF: {path}") from exc

    pages: list[DocumentPage] = []

    for page_index, pdf_page in enumerate(reader.pages):
        page_number = page_index + 1
        extraction_method = "pypdf"

        try:
            raw_text = pdf_page.extract_text() or ""
        except Exception:
            raw_text = ""

        text = normalize_text(raw_text)

        if not text:
            fallback_text = _extract_fallback(path, page_index)

            if fallback_text:
                text = normalize_text(fallback_text)
                extraction_method = "pymupdf"

        char_count = len(text)

        if char_count == 0:
            status = "needs_review"
            review_note = (
                "No extractable text. Inspect the original PDF page "
                "before deciding whether it is blank or contains visual content."
            )
        else:
            status = "needs_review"
            review_note = (
                "Text extracted. Check whether the page contains useful "
                "content before counting it toward the corpus minimum."
            )

        pages.append(
            DocumentPage(
                document_id=document_id,
                source=source,
                page=page_number,
                text=text,
                metadata={
                    "char_count": char_count,
                    "candidate_content": char_count > 0,
                    "status": status,
                    "review_note": review_note,
                    "extraction_method": extraction_method,
                    "physical_page": page_number,
                },
            )
        )

    return pages
