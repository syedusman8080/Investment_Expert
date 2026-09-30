import logging
from pathlib import Path

import chromadb

from app.models.document import TextChunk

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    def __init__(self, path: Path):
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_or_create_collection(
            "document_chunks",
            metadata={"hnsw:space": "cosine"},
        )
        self.knowledge_collection = self.client.get_or_create_collection(
            "knowledge_chunks",
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, chunks: list[TextChunk], embeddings: list[list[float]]) -> None:
        self.collection.add(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {"document_id": chunk.document_id, "page": chunk.page or -1}
                for chunk in chunks
            ],
        )

    def query(self, document_id: str, embedding: list[float], top_k: int):
        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where={"document_id": document_id},
            include=["documents", "metadatas", "distances"],
        )
        matches = []
        for index, chunk_id in enumerate(result.get("ids", [[]])[0]):
            metadata = result["metadatas"][0][index]
            matches.append(
                {
                    "chunk_id": chunk_id,
                    "text": result["documents"][0][index],
                    "page": None if metadata.get("page", -1) < 0 else metadata["page"],
                    "score": max(0.0, 1.0 - float(result["distances"][0][index])),
                }
            )
        logger.info("Retrieved chunks document_id=%s chunk_ids=%s", document_id, [m["chunk_id"] for m in matches])
        return matches

    def delete_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})

    def add_knowledge(self, chunks: list[TextChunk], embeddings: list[list[float]]) -> None:
        self.knowledge_collection.add(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.text for chunk in chunks],
            metadatas=[{"knowledge_id": chunk.document_id} for chunk in chunks],
        )

    def query_knowledge(self, embedding: list[float], top_k: int) -> list[dict]:
        result = self.knowledge_collection.query(
            query_embeddings=[embedding], n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        matches = []
        for index, chunk_id in enumerate(result.get("ids", [[]])[0]):
            matches.append({
                "chunk_id": chunk_id,
                "text": result["documents"][0][index],
                "page": None,
                "score": max(0.0, 1.0 - float(result["distances"][0][index])),
            })
        return matches
