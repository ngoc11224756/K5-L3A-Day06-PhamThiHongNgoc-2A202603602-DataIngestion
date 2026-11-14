"""Choose a real embedding provider (API or local) and implement this contract."""
from typing import Protocol

from sentence_transformers import SentenceTransformer


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class MyEmbedder:
    """Adapter cho model local qua sentence-transformers.

    Dùng intfloat/multilingual-e5-small (384 chiều). Model họ e5 yêu cầu
    tiền tố "passage: " cho văn bản được lưu trữ và "query: " cho câu hỏi
    truy vấn — bỏ tiền tố này sẽ làm giảm chất lượng truy xuất đáng kể.
    """

    def __init__(self, model_name: str = "intfloat/multilingual-e5-small") -> None:
        self.model_name = model_name
        self._model = SentenceTransformer(model_name)
        self.dimensions = self._model.get_sentence_embedding_dimension()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        prefixed = [f"passage: {t}" for t in texts]
        vectors = self._model.encode(
            prefixed, normalize_embeddings=True, show_progress_bar=False
        )
        return vectors.tolist()

    def embed_query(self, question: str) -> list[float]:
        vector = self._model.encode(
            f"query: {question}", normalize_embeddings=True, show_progress_bar=False
        )
        return vector.tolist()