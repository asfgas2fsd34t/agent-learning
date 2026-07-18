from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from agent_memory_practice.memory import Message, SQLiteConversationMemory


class MemoryTest(unittest.TestCase):
    def test_persists_messages_across_instances(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "memory.db"
            first = SQLiteConversationMemory(path)
            first.append("conv_1", Message("user", "我使用 Python"))

            second = SQLiteConversationMemory(path)

            self.assertEqual(
                second.load_recent("conv_1"),
                [Message("user", "我使用 Python")],
            )

    def test_load_recent_keeps_chronological_order(self) -> None:
        with TemporaryDirectory() as directory:
            memory = SQLiteConversationMemory(Path(directory) / "memory.db")
            memory.append("conv_1", Message("user", "第一条"))
            memory.append("conv_1", Message("assistant", "第二条"))
            memory.append("conv_1", Message("user", "第三条"))

            self.assertEqual(
                memory.load_recent("conv_1", limit=2),
                [Message("assistant", "第二条"), Message("user", "第三条")],
            )
