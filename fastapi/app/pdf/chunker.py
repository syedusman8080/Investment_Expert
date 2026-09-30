import re

from app.models.document import TextChunk


def chunk_pages(
    document_id: str,
    page_text: list[tuple[int, str]],
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
) -> list[TextChunk]:
    if chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[TextChunk] = []
    for page, text in page_text:
        normalized = re.sub(r"\s+", " ", text).strip()
        start = 0
        while start < len(normalized):
            end = min(start + chunk_size, len(normalized))
            if end < len(normalized):
                boundary = normalized.rfind(" ", start, end)
                if boundary > start + chunk_size // 2:
                    end = boundary
            content = normalized[start:end].strip()
            if content:
                chunks.append(TextChunk(f"{document_id}-{len(chunks)}", document_id, content, page))
            if end >= len(normalized):
                break
            start = end - chunk_overlap
    return chunks
