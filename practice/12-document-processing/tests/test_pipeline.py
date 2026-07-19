from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from document_processing.pipeline import load_documents, split_documents


class DocumentPipelineTest(unittest.TestCase):
    def test_loads_allowed_files_and_adds_chunk_metadata(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "guide.md").write_text("Runnable 是统一接口。" * 20, encoding="utf-8")
            (root / "secret.exe").write_text("ignored", encoding="utf-8")
            documents = load_documents(root)
            chunks = split_documents(documents, chunk_size=80, chunk_overlap=10)
            self.assertEqual(len(documents), 1)
            self.assertGreater(len(chunks), 1)
            self.assertEqual(chunks[0].metadata["source"], "guide.md")
            self.assertEqual(chunks[0].metadata["chunk_index"], 0)

    def test_rejects_invalid_overlap(self) -> None:
        with self.assertRaisesRegex(ValueError, "配置无效"):
            split_documents([], chunk_size=10, chunk_overlap=10)


if __name__ == "__main__":
    unittest.main()

