import json
from types import SimpleNamespace
import unittest

from agent_loop_practice.agent import answer_question
from agent_loop_practice.config import Settings


def response(message: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeCompletions:
    def __init__(self, responses: list[SimpleNamespace]) -> None:
        self.responses = responses
        self.requests: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.requests.append(kwargs)
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, responses: list[SimpleNamespace]) -> None:
        self.chat = SimpleNamespace(
            completions=FakeCompletions(responses)
        )


class AgentLoopTest(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings("test-key", "test-model", None)

    def test_runs_multiple_tool_rounds_until_final_answer(self) -> None:
        calls = [
            SimpleNamespace(
                id="call_1",
                type="function",
                function=SimpleNamespace(
                    name="query_sales",
                    arguments='{"month":"2026-06","region":"华东"}',
                ),
            ),
            SimpleNamespace(
                id="call_2",
                type="function",
                function=SimpleNamespace(
                    name="query_sales",
                    arguments='{"month":"2026-06","region":"华南"}',
                ),
            ),
        ]
        client = FakeClient(
            [
                response(SimpleNamespace(content=None, tool_calls=[calls[0]])),
                response(SimpleNamespace(content=None, tool_calls=[calls[1]])),
                response(
                    SimpleNamespace(
                        content="华东和华南销售额查询完成。",
                        tool_calls=None,
                    )
                ),
            ]
        )

        answer = answer_question(
            "查询华东和华南销售额",
            self.settings,
            client=client,
        )

        self.assertEqual(answer, "华东和华南销售额查询完成。")
        self.assertEqual(len(client.chat.completions.requests), 3)
        messages = client.chat.completions.requests[2]["messages"]
        self.assertEqual(
            [message["role"] for message in messages],
            ["system", "user", "assistant", "tool", "assistant", "tool"],
        )

    def test_stops_after_max_steps(self) -> None:
        call = SimpleNamespace(
            id="call_loop",
            type="function",
            function=SimpleNamespace(
                name="query_sales",
                arguments='{"month":"2026-06","region":"华东"}',
            ),
        )
        client = FakeClient(
            [
                response(SimpleNamespace(content=None, tool_calls=[call])),
                response(SimpleNamespace(content=None, tool_calls=[call])),
            ]
        )

        with self.assertRaisesRegex(RuntimeError, "超过上限"):
            answer_question("查询销售额", self.settings, client=client, max_steps=2)

        self.assertEqual(len(client.chat.completions.requests), 2)

    def test_returns_duplicate_error_without_reexecuting_tool(self) -> None:
        call = SimpleNamespace(
            id="call_repeat",
            type="function",
            function=SimpleNamespace(
                name="query_sales",
                arguments='{"month":"2026-06","region":"华东"}',
            ),
        )
        client = FakeClient(
            [
                response(SimpleNamespace(content=None, tool_calls=[call])),
                response(SimpleNamespace(content=None, tool_calls=[call])),
                response(SimpleNamespace(content="已停止重复查询。", tool_calls=None)),
            ]
        )

        answer = answer_question(
            "查询销售额",
            self.settings,
            client=client,
            max_same_call=1,
        )

        self.assertEqual(answer, "已停止重复查询。")
        messages = client.chat.completions.requests[2]["messages"]
        duplicate = json.loads(messages[-1]["content"])
        self.assertEqual(duplicate["error_code"], "DUPLICATE_TOOL_CALL")
