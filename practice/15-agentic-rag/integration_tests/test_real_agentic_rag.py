import unittest
from dotenv import load_dotenv

from agentic_rag_practice.app import build_agent, build_store, create_model


class RealAgenticRagTest(unittest.TestCase):
    def test_agent_uses_retrieval_for_knowledge_question(self) -> None:
        load_dotenv()
        result = build_agent(create_model(), build_store()).invoke({"messages": [{"role": "user", "content": "Runnable 支持哪些执行方式？"}]})
        self.assertTrue(any(message.type == "tool" for message in result["messages"]))
        self.assertTrue(result["messages"][-1].content)


if __name__ == "__main__":
    unittest.main()

