import argparse
from collections.abc import Sequence

from dotenv import load_dotenv

from .chains import summarize_text
from .config import load_settings
from .messages import build_chat_messages
from .model import create_chat_model
from .structured import extract_study_note


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LangChain 基础练习")
    parser.add_argument(
        "--mode",
        choices=("chat", "summary", "structured", "all"),
        default="summary",
        help="选择消息调用、摘要链、结构化输出或完整流程",
    )
    parser.add_argument("text", nargs="?", help="待处理内容；省略时进入输入提示")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    load_dotenv()
    model = create_chat_model(load_settings())
    text = args.text or input("请输入学习内容：").strip()

    if args.mode in {"chat", "all"}:
        response = model.invoke(build_chat_messages(text))
        if args.mode == "all":
            print("=== ChatModel 消息调用 ===")
        print(response.content)

    if args.mode in {"summary", "all"}:
        if args.mode == "all":
            print("\n=== Runnable 摘要链 ===")
        print(summarize_text(text, model))

    if args.mode in {"structured", "all"}:
        if args.mode == "all":
            print("\n=== Structured Output ===")
        note = extract_study_note(text, model)
        print(note.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
