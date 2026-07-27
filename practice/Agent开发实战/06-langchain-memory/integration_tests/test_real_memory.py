import unittest
from dotenv import load_dotenv

from lc_memory.app import build_agent, conversation_config, create_model


class RealMemoryTest(unittest.TestCase):
    def test_second_turn_uses_first_turn(self) -> None:
        load_dotenv()
        agent = build_agent(create_model())
        config = conversation_config("integration-memory")
        agent.invoke({"messages": [{"role": "user", "content": "请记住：我主要使用 Python。"}]}, config=config)
        result = agent.invoke({"messages": [{"role": "user", "content": "我主要使用什么语言？只回答语言名。"}]}, config=config)
        self.assertIn("Python", str(result["messages"][-1].content))


if __name__ == "__main__":
    unittest.main()

