from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
import sqlite3


@dataclass(frozen=True)
class Message:
    role: str
    content: str


class SQLiteConversationMemory:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversation_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_messages_conversation
                    ON conversation_messages (conversation_id, id)
                    """
                )

    def append(self, conversation_id: str, message: Message) -> None:
        if message.role not in {"user", "assistant", "tool"}:
            raise ValueError(f"不支持的消息角色：{message.role}")

        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO conversation_messages (
                        conversation_id,
                        role,
                        content
                    ) VALUES (?, ?, ?)
                    """,
                    (conversation_id, message.role, message.content),
                )

    def load_recent(self, conversation_id: str, limit: int = 20) -> list[Message]:
        if limit < 1:
            raise ValueError("limit 必须大于 0")

        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT role, content
                FROM conversation_messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (conversation_id, limit),
            ).fetchall()

        return [Message(role=row[0], content=row[1]) for row in reversed(rows)]
