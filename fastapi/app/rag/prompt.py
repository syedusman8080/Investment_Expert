from app.models.document import TextChunk


def build_grounded_prompt(question: str, chunks: list[TextChunk]) -> str:
    context = "\n\n".join(
        f"[Source {index} | page {chunk.page or 'unknown'}]\n{chunk.text}"
        for index, chunk in enumerate(chunks, 1)
    )
    return (
        "You answer questions using only the document context below. "
        "Do not invent facts or use outside knowledge. If the context does not "
        "contain the answer, say that the document does not provide enough information. "
        "Answer clearly and concisely.\n\n"
        f"DOCUMENT CONTEXT:\n{context}\n\nQUESTION:\n{question}\n\nANSWER:"
    )
