import unittest

from langgraph.types import Command

from langgraph_persistence.app import build_graph


class PersistenceTest(unittest.TestCase):
    def test_pauses_and_resumes_after_approval(self) -> None:
        graph = build_graph()
        config = {"configurable": {"thread_id": "refund_1"}}
        paused = graph.invoke({"order_id": "order_1", "amount": 100.0}, config=config)
        self.assertTrue(paused["__interrupt__"])
        completed = graph.invoke(Command(resume=True), config=config)
        self.assertEqual(completed["status"], "completed")

    def test_rejects_invalid_amount_without_approval(self) -> None:
        graph = build_graph()
        result = graph.invoke({"order_id": "order_1", "amount": 0}, config={"configurable": {"thread_id": "refund_2"}})
        self.assertEqual(result["status"], "rejected")


if __name__ == "__main__":
    unittest.main()

