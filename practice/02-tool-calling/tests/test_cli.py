import unittest

from tool_calling_practice.cli import main
from tool_calling_practice.config import Settings


class CliTest(unittest.TestCase):
    def test_reads_question_and_prints_answer(self) -> None:
        settings = Settings(api_key="test-key", model="test-model", base_url=None)
        outputs: list[str] = []

        main(
            input_fn=lambda _: "查询 2026 年 6 月华东区销售额",
            output_fn=outputs.append,
            settings_loader=lambda: settings,
            answer=lambda question, received_settings: "销售额为 125 万元",
            load_env=lambda: None,
        )

        self.assertEqual(outputs, ["\n助手回答：\n销售额为 125 万元"])


if __name__ == "__main__":
    unittest.main()
