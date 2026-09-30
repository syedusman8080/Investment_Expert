from app.models.document import TextChunk
from app.rag.prompt import build_grounded_prompt
from app.services.rag_service import RagService


def test_prompt_is_grounded_and_includes_page_context():
    prompt = build_grounded_prompt("What is the answer?", [TextChunk("c1", "d1", "The answer is local.", 2)])
    assert "only the document context" in prompt
    assert "page 2" in prompt
    assert "What is the answer?" in prompt


def test_rag_service_embeds_retrieves_and_generates():
    class Embeddings:
        def encode(self, texts):
            return [[1.0, 0.0] for _ in texts]

    class Store:
        def query(self, document_id, embedding, top_k):
            return [{"chunk_id": "c1", "text": "Context", "page": 1, "score": 0.9}]

    class Llm:
        def generate(self, prompt):
            assert "Context" in prompt
            return "Answer"

    answer, sources = RagService(Embeddings(), Store(), Llm(), 2).answer("d1", "Question")
    assert answer == "Answer"
    assert sources[0]["page"] == 1
