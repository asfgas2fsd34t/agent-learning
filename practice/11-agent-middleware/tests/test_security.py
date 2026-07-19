import unittest

from agent_middleware_practice.app import authorize_region, create_query_tool


class SecurityTest(unittest.TestCase):
    def test_permission_is_derived_from_server_user(self) -> None:
        self.assertTrue(authorize_region("user_1", "华东"))
        self.assertFalse(authorize_region("user_1", "华南"))

    def test_tool_returns_non_retryable_forbidden(self) -> None:
        result = create_query_tool("user_1").invoke({"month": "2026-06", "region": "华南"})
        self.assertEqual(result["error_code"], "FORBIDDEN")
        self.assertFalse(result["retryable"])


if __name__ == "__main__":
    unittest.main()

