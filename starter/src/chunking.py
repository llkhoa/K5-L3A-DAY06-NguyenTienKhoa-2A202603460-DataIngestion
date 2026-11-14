
"""Fixed-size and paragraph-aware chunking strategies."""

import hashlib

from .models import Chunk, DocumentPage


def _make_chunk(
    page: DocumentPage,
    text: str,
    strategy: str,
    index: int,
    start: int,
    end: int,
) -> Chunk:
    """Create a chunk while preserving its source traceability."""

    text = text.strip()

    if not text:
        raise ValueError("Cannot create an empty chunk.")

    # Stable ID: same source, page, strategy and text -> same ID.
    identity = (
        f"{page.document_id}|{page.page}|{strategy}|"
        f"{start}|{end}|{text}"
    )
    chunk_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]

    metadata = dict(page.metadata or {})
    metadata.update({
        "chunking_strategy": strategy,
        "chunk_index": index,
        "char_start": start,
        "char_end": end,
        "page": page.page,
    })

    return Chunk(
        chunk_id=chunk_id,
        document_id=page.document_id,
        source=page.source,
        page=page.page,
        text=text,
        metadata=metadata,
    )


def fixed_size(
    page: DocumentPage,
    size: int,
    overlap: int
) -> list[Chunk]:
    """Split a page into fixed-size overlapping character windows."""

    if size <= 0:
        raise ValueError("size must be greater than 0.")

    if overlap < 0:
        raise ValueError("overlap cannot be negative.")

    if overlap >= size:
        raise ValueError("overlap must be smaller than size.")

    text = page.text or ""

    if not text.strip():
        return []

    chunks: list[Chunk] = []
    step = size - overlap
    start = 0
    index = 0

    while start < len(text):
        end = min(start + size, len(text))
        raw_chunk = text[start:end]

        # Adjust offsets if trimming leading/trailing whitespace.
        leading = len(raw_chunk) - len(raw_chunk.lstrip())
        trailing = len(raw_chunk.rstrip())

        chunk_text = raw_chunk.strip()

        if chunk_text:
            actual_start = start + leading
            actual_end = start + trailing

            chunks.append(
                _make_chunk(
                    page=page,
                    text=chunk_text,
                    strategy="fixed",
                    index=index,
                    start=actual_start,
                    end=actual_end,
                )
            )
            index += 1

        if end == len(text):
            break

        start += step

    return chunks


def _paragraph_spans(text: str) -> list[tuple[int, int]]:
    """Return paragraph start/end offsets in the original page text."""

    import re

    # Split at blank-line boundaries while retaining original offsets.
    pattern = r"\S.*?(?=\n\s*\n|\Z)"

    return [
        (match.start(), match.end())
        for match in re.finditer(pattern, text, flags=re.DOTALL)
    ]


def by_paragraph(
    page: DocumentPage,
    max_size: int
) -> list[Chunk]:
    """Group paragraphs while keeping chunks within max_size.

    Paragraphs are kept together whenever possible.
    Oversized paragraphs are split into contiguous character windows.
    """

    if max_size <= 0:
        raise ValueError("max_size must be greater than 0.")

    text = page.text or ""

    if not text.strip():
        return []

    spans = _paragraph_spans(text)

    chunks: list[Chunk] = []
    index = 0

    current_parts: list[str] = []
    current_start: int | None = None
    current_end: int | None = None

    def flush_current() -> None:
        nonlocal index, current_parts, current_start, current_end

        if not current_parts:
            return

        chunk_text = "\n\n".join(current_parts)

        chunks.append(
            _make_chunk(
                page=page,
                text=chunk_text,
                strategy="paragraph",
                index=index,
                start=current_start,
                end=current_end,
            )
        )

        index += 1
        current_parts = []
        current_start = None
        current_end = None

    for paragraph_start, paragraph_end in spans:
        paragraph = text[paragraph_start:paragraph_end].strip()

        if not paragraph:
            continue

        # A paragraph larger than max_size must be split.
        if len(paragraph) > max_size:
            flush_current()

            position = 0

            while position < len(paragraph):
                part = paragraph[position:position + max_size]

                if part.strip():
                    actual_start = paragraph_start + position
                    actual_end = actual_start + len(part)

                    chunks.append(
                        _make_chunk(
                            page=page,
                            text=part,
                            strategy="paragraph",
                            index=index,
                            start=actual_start,
                            end=actual_end,
                        )
                    )
                    index += 1

                position += max_size

            continue

        # Try adding this paragraph to the current chunk.
        if current_parts:
            candidate_length = (
                sum(len(part) for part in current_parts)
                + 2 * len(current_parts)
                + len(paragraph)
            )

            if candidate_length > max_size:
                flush_current()

        if current_start is None:
            current_start = paragraph_start

        current_end = paragraph_end
        current_parts.append(paragraph)

    flush_current()

    return chunks
