import unittest

from lc_tools.app import query_sales


class ToolTest(unittest.TestCase):
    def test_schema_and_success_result(self) -> None:
        schema = query_sales.args_schema.model_json_schema()
        self.assertEqual(set(schema["required"]), {"month", "region"})
        result = query_sales.invoke({"month": "2026-06", "region": "华东"})
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["amount"], 128000.0)

    def test_invalid_month_is_not_retryable(self) -> None:
        result = query_sales.invoke({"month": "六月", "region": "华东"})
        self.assertEqual(result["error_code"], "INVALID_MONTH")
        self.assertFalse(result["retryable"])


if __name__ == "__main__":
    unittest.main()

