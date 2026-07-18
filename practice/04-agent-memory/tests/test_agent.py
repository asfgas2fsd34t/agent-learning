from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from agent_memory_practice.agent import answer_question
from agent_memory_practice.config import Settings
from agent_memory_practice.memory import SQLiteConversationMemory


class FakeCompletions:
    def __init__(self, answers: list[str]) -> None:
        self.answers = answers
        self.requests: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.requests.append(kwargs)
        message = SimpleNamespace(content=self.answers.pop(0))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class AgentMemoryTest(unittest.TestCase):
    def test_second_turn_contains_first_turn_history(self) -> None:
        with TemporaryDirectory() as directory:
            memory = SQLiteConversationMemory(Path(directory) / "memory.db")
            completions = FakeCompletions(["记住了", "你使用 Java"])
            client = SimpleNamespace(
                chat=SimpleNamespace(completions=completions)
            )
            settings = Settings("test-key", "test-model", None)

            answer_question(
                "conv_1",
                "我使用 Java",
                settings,
                memory,
                client=client,
            )
            answer = answer_question(
                "conv_1",
                "我使用什么语言？",
                settings,
                memory,
                client=client,
            )

            self.assertEqual(answer, "你使用 Java")
            second_messages = completions.requests[1]["messages"]
            self.assertEqual(
                [message["content"] for message in second_messages],
                [
                    "你是一名简洁、准确的 Agent 开发助手。",
                    "我使用 Java",
                    "记住了",
                    "我使用什么语言？",
                ],
            )


if __name__ == "__main__":
    unittest.main()
