from contextlib import redirect_stdout
from io import StringIO
import unittest

from langchain_basics.cli import main


SOURCE_TEXT = (
    "Runnable 是 LangChain 的统一执行协议。"
    "提示词模板、聊天模型和输出解析器都可以作为 Runnable，"
    "并使用竖线运算符组合成一条执行链。"
)


class CompleteLangChainFlowTest(unittest.TestCase):
    def test_real_model_runs_the_complete_learning_flow(self) -> None:
        output_buffer = StringIO()
        with redirect_stdout(output_buffer):
            main(["--mode", "all", SOURCE_TEXT])

        output = output_buffer.getvalue()
        print(output)
        self.assertIn("=== ChatModel 消息调用 ===", output)
        self.assertIn("=== Runnable 摘要链 ===", output)
        self.assertIn("=== Structured Output ===", output)
        self.assertIn('"topic"', output)
        self.assertIn('"key_points"', output)
        self.assertIn('"summary"', output)


if __name__ == "__main__":
    unittest.main()
