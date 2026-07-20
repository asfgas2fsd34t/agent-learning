import unittest

from tool_calling_practice.tools import SALES_TOOL, execute_tool


class ToolDefinitionTest(unittest.TestCase):
    def test_sales_tool_requires_month_and_region(self) -> None:
        function = SALES_TOOL["function"]

        self.assertEqual(function["name"], "query_sales")
        self.assertEqual(
            function["parameters"]["required"],
            ["month", "region"],
        )

    def test_execute_tool_rejects_unknown_tool(self) -> None:
        result = execute_tool("delete_sales", {})

        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "UNKNOWN_TOOL")


if __name__ == "__main__":
    unittest.main()
