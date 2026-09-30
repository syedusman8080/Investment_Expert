from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    document_id: str
    text: str
    page: int | None
