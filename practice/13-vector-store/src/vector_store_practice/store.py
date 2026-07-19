import hashlib
import math

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore


class HashEmbeddings(Embeddings):
    """用于离线理解接口的确定性 Embedding，不代表生产语义效果。"""

    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = [text[index:index + 2].lower() for index in range(max(1, len(text) - 1))]
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            vector[int.from_bytes(digest[:4], "big") % self.dimensions] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def build_store(documents: list[Document]) -> InMemoryVectorStore:
    store = InMemoryVectorStore(HashEmbeddings())
    store.add_documents(documents)
    return store

