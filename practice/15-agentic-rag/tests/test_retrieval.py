import unittest

from agentic_rag_practice.app import build_store, retrieve_documents


class RetrievalTest(unittest.TestCase):
    def test_artifact_keeps_source_documents(self) -> None:
        content, documents = retrieve_documents(build_store(), "Runnable")
        self.assertTrue(content)
        self.assertEqual(len(documents), 2)
        self.assertTrue(all("source" in document.metadata for document in documents))


if __name__ == "__main__":
    unittest.main()

