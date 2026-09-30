import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_path: Path):
        self.model_path = model_path
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(str(self.model_path))
            except Exception as exc:
                raise RuntimeError(
                    f"Embedding model unavailable at '{self.model_path}'. "
                    "Download a local Sentence Transformers model and set EMBEDDING_MODEL_PATH."
                ) from exc
        return self._model

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._load()
        vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return vectors.tolist()


@lru_cache
def get_embedding_service(model_path: str) -> EmbeddingService:
    return EmbeddingService(Path(model_path))
