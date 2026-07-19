import unittest
from dotenv import load_dotenv

from lc_agent.app import build_agent, create_model


class RealAgentTest(unittest.TestCase):
    def test_agent_uses_multiple_tool_calls(self) -> None:
        load_dotenv()
        result = build_agent(create_model()).invoke({"messages": [{"role": "user", "content": "比较 2026-06 华东和华南销售额"}]})
        tool_messages = [message for message in result["messages"] if message.type == "tool"]
        self.assertGreaterEqual(len(tool_messages), 2)
        self.assertTrue(result["messages"][-1].content)


if __name__ == "__main__":
    unittest.main()

