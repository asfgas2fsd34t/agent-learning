from types import SimpleNamespace
import unittest

from llm_api_practice.chat import ask_model
from llm_api_practice.config import Settings


class FakeCompletions:
    def __init__(self, content: str | None = "这是模型回答") -> None:
        self.request: dict[str, object] | None = None
        self.content = content

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.request = kwargs
        message = SimpleNamespace(content=self.content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeClient:
    def __init__(self, content: str | None = "这是模型回答") -> None:
        self.completions = FakeCompletions(content)
        self.chat = SimpleNamespace(completions=self.completions)


class AskModelTest(unittest.TestCase):
    def test_sends_question_and_returns_content(self) -> None:
        settings = Settings(api_key="test-key", model="test-model", base_url=None)
        client = FakeClient()

        answer = ask_model("什么是 Agent？", settings, client=client)

        self.assertEqual(answer, "这是模型回答")
        self.assertEqual(
            client.completions.request,
            {
                "model": "test-model",
                "messages": [
                    {"role": "system", "content": "你是一名耐心、准确的 Agent 开发导师。"},
                    {"role": "user", "content": "什么是 Agent？"},
                ],
            },
        )

    def test_rejects_empty_model_response(self) -> None:
        settings = Settings(api_key="test-key", model="test-model", base_url=None)

        with self.assertRaisesRegex(ValueError, "空内容"):
            ask_model("什么是 Agent？", settings, client=FakeClient(content=None))


if __name__ == "__main__":
    unittest.main()
