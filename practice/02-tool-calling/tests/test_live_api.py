import os
import unittest

from dotenv import load_dotenv

from tool_calling_practice.agent import answer_question
from tool_calling_practice.config import load_settings


load_dotenv()


@unittest.skipUnless(
    os.getenv("RUN_LIVE_TESTS") == "1",
    "设置 RUN_LIVE_TESTS=1 后运行真实模型测试",
)
class LiveApiTest(unittest.TestCase):
    def test_real_model_and_tool_calling(self) -> None:
        settings = load_settings()
        answer = answer_question(
            "请查询 2026 年 6 月华东区销售额，并说明查询结果。",
            settings,
        )

        self.assertTrue(answer.strip())
        self.assertIn("1250000", answer.replace(",", "").replace("，", ""))


if __name__ == "__main__":
    unittest.main()
