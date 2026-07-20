import unittest

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from rag_chain_practice.app import build_store, create_rag_chain, format_context


class RagChainTest(unittest.TestCase):
    def test_context_contains_sources(self) -> None:
        context = format_context(build_store(), {"question": "Runnable 是什么"})
        self.assertIn("source=", context)
        self.assertIn("Runnable", context)

    def test_chain_returns_model_text(self) -> None:
        model = RunnableLambda(lambda prompt: AIMessage(content="Runnable 是统一协议 [runnable.md]"))
        result = create_rag_chain(model, build_store()).invoke({"question": "Runnable 是什么"})
        self.assertIn("runnable.md", result)


if __name__ == "__main__":
    unittest.main()

