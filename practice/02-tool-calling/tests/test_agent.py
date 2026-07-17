import json
from types import SimpleNamespace
import unittest

from tool_calling_practice.agent import answer_question
from tool_calling_practice.config import Settings


class FakeCompletions:
    def __init__(self, responses: list[SimpleNamespace]) -> None:
        self.responses = responses
        self.requests: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.requests.append(kwargs)
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, responses: list[SimpleNamespace]) -> None:
        self.completions = FakeCompletions(responses)
        self.chat = SimpleNamespace(completions=self.completions)


def model_response(message: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class AnswerQuestionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            api_key="test-key",
            model="test-model",
            base_url=None,
        )

    def test_executes_requested_tool_and_returns_final_answer(self) -> None:
        tool_call = SimpleNamespace(
            id="call_1",
            type="function",
            function=SimpleNamespace(
                name="query_sales",
                arguments='{"month":"2026-06","region":"华东"}',
            ),
        )
        first_message = SimpleNamespace(content=None, tool_calls=[tool_call])
        final_message = SimpleNamespace(
            content="2026 年 6 月华东区销售额为 125 万元。",
            tool_calls=None,
        )
        client = FakeClient(
            [model_response(first_message), model_response(final_message)]
        )

        answer = answer_question(
            "查询 2026 年 6 月华东区销售额",
            self.settings,
            client=client,
        )

        self.assertEqual(answer, "2026 年 6 月华东区销售额为 125 万元。")
        self.assertEqual(len(client.completions.requests), 2)

        second_messages = client.completions.requests[1]["messages"]
        self.assertEqual(
            [message["role"] for message in second_messages],
            ["system", "user", "assistant", "tool"],
        )
        tool_result = json.loads(second_messages[-1]["content"])
        self.assertEqual(tool_result["data"]["sales"], 1250000)
        self.assertEqual(second_messages[-1]["tool_call_id"], "call_1")

    def test_returns_direct_answer_when_model_does_not_request_tool(self) -> None:
        message = SimpleNamespace(
            content="你好，我可以查询销售额。",
            tool_calls=None,
        )
        client = FakeClient([model_response(message)])

        answer = answer_question("你好", self.settings, client=client)

        self.assertEqual(answer, "你好，我可以查询销售额。")
        self.assertEqual(len(client.completions.requests), 1)


if __name__ == "__main__":
    unittest.main()
