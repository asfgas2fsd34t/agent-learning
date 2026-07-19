import unittest
from dotenv import load_dotenv

from lc_tools.app import create_model, run_tool_conversation


class RealToolFlowTest(unittest.TestCase):
    def test_model_calls_sales_tool(self) -> None:
        load_dotenv()
        answer = run_tool_conversation("查询 2026-06 华东销售额", create_model())
        self.assertIn("128", answer)


if __name__ == "__main__":
    unittest.main()

