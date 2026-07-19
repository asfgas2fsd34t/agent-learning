import unittest

from lc_memory.app import conversation_config


class ConversationConfigTest(unittest.TestCase):
    def test_builds_stable_thread_config(self) -> None:
        self.assertEqual(conversation_config("conv_1"), {"configurable": {"thread_id": "conv_1"}})

    def test_rejects_empty_thread_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "不能为空"):
            conversation_config(" ")


if __name__ == "__main__":
    unittest.main()

