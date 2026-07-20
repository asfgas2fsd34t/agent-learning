import unittest

from tool_calling_practice.sales import query_sales


class QuerySalesTest(unittest.TestCase):
    def test_returns_sales_for_known_month_and_region(self) -> None:
        result = query_sales(month="2026-06", region="华东")

        self.assertEqual(
            result,
            {
                "success": True,
                "data": {
                    "month": "2026-06",
                    "region": "华东",
                    "sales": 1250000,
                    "currency": "CNY",
                    "unit": "元",
                },
            },
        )

    def test_rejects_invalid_month(self) -> None:
        result = query_sales(month="下个月", region="华东")

        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "INVALID_MONTH")

    def test_rejects_unknown_region(self) -> None:
        result = query_sales(month="2026-06", region="全部地区")

        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "INVALID_REGION")

    def test_returns_no_data_for_valid_but_missing_period(self) -> None:
        result = query_sales(month="2026-07", region="华东")

        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "NO_DATA")


if __name__ == "__main__":
    unittest.main()
