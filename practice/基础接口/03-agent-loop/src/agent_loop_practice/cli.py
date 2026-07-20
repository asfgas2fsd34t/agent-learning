from dotenv import load_dotenv

from .agent import answer_question
from .config import load_settings


def main() -> None:
    load_dotenv()
    settings = load_settings()
    question = input("请输入问题：")
    print(answer_question(question, settings))


if __name__ == "__main__":
    main()
