from datetime import datetime, timezone
from uuid import uuid4

from app.core.config import Settings
from app.db import KnowledgeSource
from app.embeddings.service import EmbeddingService
from app.models.document import TextChunk
from app.pdf.chunker import chunk_pages
from app.pdf.extractor import extract_pdf
from app.vectorstore.chroma import ChromaVectorStore


class KnowledgeService:
    def __init__(self, settings: Settings, embeddings: EmbeddingService, vector_store: ChromaVectorStore):
        self.settings = settings
        self.embeddings = embeddings
        self.vector_store = vector_store

    def add_text(self, title: str, content: str, user_id: int, db) -> KnowledgeSource:
        knowledge_id = uuid4().hex
        chunks = chunk_pages(
            knowledge_id, [(1, content)], self.settings.chunk_size, self.settings.chunk_overlap
        )
        self.vector_store.add_knowledge(chunks, self.embeddings.encode([chunk.text for chunk in chunks]))
        source = KnowledgeSource(
            title=title, source_type="text", created_by=user_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    def add_pdf(self, title: str, data: bytes, user_id: int, db) -> KnowledgeSource:
        extracted = extract_pdf(data)
        knowledge_id = uuid4().hex
        chunks = chunk_pages(
            knowledge_id, extracted.page_text, self.settings.chunk_size, self.settings.chunk_overlap
        )
        self.vector_store.add_knowledge(chunks, self.embeddings.encode([chunk.text for chunk in chunks]))
        source = KnowledgeSource(
            title=title, source_type="pdf", created_by=user_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source
