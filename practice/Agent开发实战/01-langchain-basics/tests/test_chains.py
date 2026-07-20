import unittest

from langchain_core.messages import AIMessage
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.runnables import RunnableLambda

from langchain_basics.chains import summarize_text


class SummaryChainTest(unittest.TestCase):
    def test_formats_prompt_and_parses_ai_message(self) -> None:
        received_prompts: list[ChatPromptValue] = []

        def fake_model(prompt: ChatPromptValue) -> AIMessage:
            received_prompts.append(prompt)
            return AIMessage(content="1. 统一接口\n2. 可组合\n3. 可测试")

        answer = summarize_text(
            "LangChain 提供统一的 Runnable 接口。",
            RunnableLambda(fake_model),
        )

        self.assertEqual(answer, "1. 统一接口\n2. 可组合\n3. 可测试")
        self.assertIn(
            "LangChain 提供统一的 Runnable 接口。",
            received_prompts[0].messages[-1].content,
        )

    def test_rejects_empty_text(self) -> None:
        with self.assertRaisesRegex(ValueError, "不能为空"):
            summarize_text(" ", RunnableLambda(lambda value: value))


if __name__ == "__main__":
    unittest.main()

