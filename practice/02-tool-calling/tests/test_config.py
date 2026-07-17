import os
import unittest
from unittest.mock import patch

from tool_calling_practice.config import ConfigurationError, load_settings


class LoadSettingsTest(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_requires_api_key(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "LLM_API_KEY"):
            load_settings()

    @patch.dict(os.environ, {"LLM_API_KEY": "test-key"}, clear=True)
    def test_requires_model(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "LLM_MODEL"):
            load_settings()

    @patch.dict(
        os.environ,
        {
            "LLM_API_KEY": "test-key",
            "LLM_MODEL": "test-model",
            "LLM_BASE_URL": "https://example.com/v1",
        },
        clear=True,
    )
    def test_reads_environment(self) -> None:
        settings = load_settings()

        self.assertEqual(settings.api_key, "test-key")
        self.assertEqual(settings.model, "test-model")
        self.assertEqual(settings.base_url, "https://example.com/v1")


if __name__ == "__main__":
    unittest.main()
