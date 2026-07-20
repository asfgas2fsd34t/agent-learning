import unittest

from langgraph_workflow.app import build_graph


class WorkflowTest(unittest.TestCase):
    def test_routes_knowledge_question(self) -> None:
        result = build_graph().invoke({"question": "Runnable 是什么？", "attempts": 0})
        self.assertEqual(result["route"], "knowledge")
        self.assertIn("统一执行协议", result["answer"])

    def test_direct_question_skips_retrieval(self) -> None:
        result = build_graph().invoke({"question": "你好", "attempts": 0})
        self.assertEqual(result["route"], "direct")
        self.assertEqual(result["attempts"], 0)


if __name__ == "__main__":
    unittest.main()

