import unittest
from dotenv import load_dotenv

from rag_chain_practice.app import build_store, create_model, create_rag_chain


class RealRagTest(unittest.TestCase):
    def test_answer_contains_source(self) -> None:
        load_dotenv()
        answer = create_rag_chain(create_model(), build_store()).invoke({"question": "Runnable 支持哪些执行方式？"})
        self.assertIn("runnable.md", answer)


if __name__ == "__main__":
    unittest.main()

