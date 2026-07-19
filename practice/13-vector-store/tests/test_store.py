import unittest

from langchain_core.documents import Document

from vector_store_practice.store import build_store


class VectorStoreTest(unittest.TestCase):
    def test_retrieves_related_document(self) -> None:
        store = build_store([
            Document(page_content="Runnable 是 LangChain 的统一执行接口", metadata={"source": "runnable.md"}),
            Document(page_content="退款操作需要业务幂等键", metadata={"source": "refund.md"}),
        ])
        result = store.similarity_search("Runnable 统一执行", k=1)
        self.assertEqual(result[0].metadata["source"], "runnable.md")


if __name__ == "__main__":
    unittest.main()

