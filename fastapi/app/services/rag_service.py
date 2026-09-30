from app.embeddings.service import EmbeddingService
from app.llm.service import LLMService
from app.rag.prompt import build_grounded_prompt
from app.vectorstore.chroma import ChromaVectorStore


class RagService:
    def __init__(self, embeddings: EmbeddingService, vector_store: ChromaVectorStore, llm: LLMService, top_k: int):
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.llm = llm
        self.top_k = top_k

    def answer(self, document_id: str, question: str) -> tuple[str, list[dict]]:
        question_embedding = self.embeddings.encode([question])[0]
        sources = self.vector_store.query(document_id, question_embedding, self.top_k)
        from app.models.document import TextChunk
        context_chunks = [
            TextChunk(source["chunk_id"], document_id, source["text"], source["page"])
            for source in sources
        ]
        answer = self.llm.generate(build_grounded_prompt(question, context_chunks))
        return answer, sources
