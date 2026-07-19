from pathlib import Path
import unittest

from dotenv import load_dotenv

from langchain_runnables.chains import create_adaptive_summary_chain
from langchain_runnables.cli import LONG_TEXT, SHORT_TEXT
from langchain_runnables.config import load_settings
from langchain_runnables.model import create_chat_model


class RealRunnableFlowTest(unittest.TestCase):
    def test_real_model_supports_invoke_batch_and_stream(self) -> None:
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        chain = create_adaptive_summary_chain(
            create_chat_model(load_settings())
        )

        single = chain.invoke({"text": SHORT_TEXT})
        self.assertTrue(single.strip())

        batch = chain.batch(
            [
                {"text": SHORT_TEXT},
                {"text": LONG_TEXT},
            ]
        )
        self.assertEqual(len(batch), 2)
        self.assertTrue(all(item.strip() for item in batch))

        streamed = "".join(
            chain.stream({"text": "请流式总结 Runnable 的作用。"})
        )
        self.assertTrue(streamed.strip())


if __name__ == "__main__":
    unittest.main()
