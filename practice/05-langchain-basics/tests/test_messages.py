import unittest

from langchain.messages import HumanMessage, SystemMessage

from langchain_basics.messages import SYSTEM_PROMPT, build_chat_messages


class BuildChatMessagesTest(unittest.TestCase):
    def test_builds_system_and_human_messages(self) -> None:
        messages = build_chat_messages("什么是 Runnable？")

        self.assertIsInstance(messages[0], SystemMessage)
        self.assertEqual(messages[0].content, SYSTEM_PROMPT)
        self.assertIsInstance(messages[1], HumanMessage)
        self.assertEqual(messages[1].content, "什么是 Runnable？")

    def test_rejects_empty_question(self) -> None:
        with self.assertRaisesRegex(ValueError, "不能为空"):
            build_chat_messages("   ")


if __name__ == "__main__":
    unittest.main()
