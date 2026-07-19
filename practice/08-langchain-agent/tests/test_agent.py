import unittest

from lc_agent.app import query_sales


class AgentToolTest(unittest.TestCase):
    def test_query_sales_is_deterministic(self) -> None:
        first = query_sales.invoke({"month": "2026-06", "region": "华东"})
        second = query_sales.invoke({"month": "2026-06", "region": "华东"})
        self.assertEqual(first, second)
        self.assertEqual(first["amount"], 128000.0)


if __name__ == "__main__":
    unittest.main()

