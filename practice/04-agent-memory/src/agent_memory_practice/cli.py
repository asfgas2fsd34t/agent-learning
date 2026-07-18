from pathlib import Path

from dotenv import load_dotenv

from .agent import answer_question
from .config import load_settings
from .memory import SQLiteConversationMemory


def main() -> None:
    load_dotenv()
    settings = load_settings()
    data_directory = Path(".data")
    data_directory.mkdir(exist_ok=True)
    memory = SQLiteConversationMemory(data_directory / "memory.db")
    conversation_id = input("请输入会话 ID：").strip() or "default"

    while True:
        question = input("\n你：").strip()
        if question.lower() in {"exit", "quit", "退出"}:
            break
        if not question:
            continue

        answer = answer_question(conversation_id, question, settings, memory)
        print(f"助手：{answer}")


if __name__ == "__main__":
    main()
