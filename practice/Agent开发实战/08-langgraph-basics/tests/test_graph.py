import unittest

from langgraph_basics.app import build_graph


class GraphTest(unittest.TestCase):
    def test_runs_plan_then_write(self) -> None:
        graph = build_graph(lambda prompt: f"收到：{prompt}")
        result = graph.invoke({"topic": "Runnable"})
        self.assertEqual(len(result["outline"]), 3)
        self.assertIn("Runnable", result["draft"])


if __name__ == "__main__":
    unittest.main()

