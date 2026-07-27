import unittest

from langsmith_practice.tracing import (
    build_trace_config,
    invoke_observed,
)


class TracingTest(unittest.TestCase):
    def test_trace_config_contains_stable_run_metadata(self) -> None:
        config = build_trace_config("req-001", "test")

        self.assertEqual(config["run_name"], "langsmith_learning_chain")
        self.assertIn("runnable", config["tags"])
        self.assertEqual(config["metadata"]["request_id"], "req-001")
        self.assertEqual(config["metadata"]["environment"], "test")

    def test_invoke_does_not_require_langsmith_network(self) -> None:
        result = invoke_observed("  什么是 Agent？  ", request_id="req-002")

        self.assertEqual(result, "收到问题：什么是 Agent？")


if __name__ == "__main__":
    unittest.main()
