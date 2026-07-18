import unittest

from agent_loop_practice.tools import execute_tool, tool_call_signature


class ToolTest(unittest.TestCase):
    def test_queries_known_sales(self) -> None:
        result = execute_tool(
            "query_sales",
            {"month": "2026-06", "region": "华东"},
        )

        self.assertEqual(result["data"]["sales"], 1_250_000)

    def test_unknown_tool_returns_non_retryable_error(self) -> None:
        result = execute_tool("missing_tool", {})

        self.assertEqual(result["error_code"], "UNKNOWN_TOOL")
        self.assertFalse(result["retryable"])

    def test_signature_changes_when_arguments_change(self) -> None:
        east = tool_call_signature("query_sales", {"region": "华东"})
        south = tool_call_signature("query_sales", {"region": "华南"})

        self.assertNotEqual(east, south)
