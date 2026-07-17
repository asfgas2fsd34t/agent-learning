import unittest

from llm_api_practice.cli import main
from llm_api_practice.config import Settings


class CliTest(unittest.TestCase):
    def test_reads_question_and_prints_answer(self) -> None:
        settings = Settings(api_key="test-key", model="test-model", base_url=None)
        outputs: list[str] = []
        questions: list[str] = []

        def fake_ask(question: str, received_settings: Settings) -> str:
            questions.append(question)
            self.assertEqual(received_settings, settings)
            return "模型回答"

        main(
            input_fn=lambda _: "什么是 Agent？",
            output_fn=outputs.append,
            settings_loader=lambda: settings,
            ask=fake_ask,
            load_env=lambda: None,
        )

        self.assertEqual(questions, ["什么是 Agent？"])
        self.assertEqual(outputs, ["\n模型回答：\n模型回答"])


if __name__ == "__main__":
    unittest.main()
