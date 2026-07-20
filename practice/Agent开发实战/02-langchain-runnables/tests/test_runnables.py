import unittest

from langchain_core.messages import AIMessage
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.runnables import RunnableLambda

from langchain_runnables.chains import create_adaptive_summary_chain
from langchain_runnables.runnables import create_preparation_chain


class PreparationChainTest(unittest.TestCase):
    def test_preserves_input_and_adds_parallel_features(self) -> None:
        result = create_preparation_chain().invoke(
            {"text": "  Runnable   是统一接口  "}
        )

        self.assertEqual(result["text"], "  Runnable   是统一接口  ")
        self.assertEqual(result["normalized_text"], "Runnable 是统一接口")
        self.assertEqual(result["text_length"], 14)

    def test_rejects_empty_text(self) -> None:
        with self.assertRaisesRegex(ValueError, "不能为空"):
            create_preparation_chain().invoke({"text": "  "})


class AdaptiveSummaryChainTest(unittest.TestCase):
    def test_short_and_long_inputs_use_different_branches(self) -> None:
        def fake_model(prompt: ChatPromptValue) -> AIMessage:
            content = prompt.messages[-1].content
            if "详细总结" in content:
                return AIMessage(content="long branch")
            return AIMessage(content="short branch")

        chain = create_adaptive_summary_chain(RunnableLambda(fake_model))

        self.assertEqual(
            chain.invoke({"text": "短内容"}),
            "short branch",
        )
        self.assertEqual(
            chain.invoke({"text": "长内容 " * 30}),
            "long branch",
        )

    def test_batch_runs_the_same_chain_for_multiple_inputs(self) -> None:
        fake_model = RunnableLambda(
            lambda prompt: AIMessage(content="摘要")
        )
        chain = create_adaptive_summary_chain(fake_model)

        results = chain.batch(
            [{"text": "第一段"}, {"text": "第二段"}]
        )

        self.assertEqual(results, ["摘要", "摘要"])


if __name__ == "__main__":
    unittest.main()
