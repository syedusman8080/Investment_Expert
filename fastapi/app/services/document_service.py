import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.config import Settings
from app.embeddings.service import EmbeddingService
from app.models.document import TextChunk
from app.pdf.chunker import chunk_pages
from app.pdf.extractor import extract_pdf
from app.vectorstore.chroma import ChromaVectorStore

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, settings: Settings, embeddings: EmbeddingService, vector_store: ChromaVectorStore):
        self.settings = settings
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.storage = settings.resolve_path(settings.document_storage_path)
        self.storage.mkdir(parents=True, exist_ok=True)
        self.index_path = self.storage / "index.json"

    def _read_index(self) -> list[dict]:
        if not self.index_path.exists():
            return []
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def _write_index(self, documents: list[dict]) -> None:
        self.index_path.write_text(json.dumps(documents, indent=2), encoding="utf-8")

    def list_documents(self) -> list[dict]:
        return self._read_index()

    def process(self, filename: str, data: bytes) -> dict:
        document_id = uuid4().hex
        extracted = extract_pdf(data)
        chunks = chunk_pages(
            document_id,
            extracted.page_text,
            self.settings.chunk_size,
            self.settings.chunk_overlap,
        )
        embeddings = self.embeddings.encode([chunk.text for chunk in chunks])
        self.vector_store.add(chunks, embeddings)
        path = self.storage / f"{document_id}.pdf"
        path.write_bytes(data)
        record = {
            "document_id": document_id,
            "filename": filename,
            "pages": extracted.pages,
            "characters": extracted.characters,
            "chunks": len(chunks),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        documents = self._read_index()
        documents.append(record)
        self._write_index(documents)
        logger.info(
            "Document processed document_id=%s pages=%s characters=%s chunks=%s",
            document_id, extracted.pages, extracted.characters, len(chunks),
        )
        return record

    def delete(self, document_id: str) -> None:
        documents = self._read_index()
        if not any(item["document_id"] == document_id for item in documents):
            raise KeyError(document_id)
        self.vector_store.delete_document(document_id)
        path = self.storage / f"{document_id}.pdf"
        if path.exists():
            path.unlink()
        self._write_index([item for item in documents if item["document_id"] != document_id])
