import argparse
from collections.abc import Sequence

from dotenv import load_dotenv

from .chains import create_adaptive_summary_chain
from .config import load_settings
from .model import create_chat_model


SHORT_TEXT = "Runnable 是 LangChain 的统一执行协议。"
LONG_TEXT = (
    "Runnable 是 LangChain 的统一执行协议。提示词模板、聊天模型和输出解析器都可以作为 Runnable，"
    "并使用竖线运算符组合成一条执行链。Runnable 还提供 invoke、batch、stream 和 ainvoke 等统一接口，"
    "让程序可以用同一种方式执行单次、批量、流式和异步任务。"
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Runnable 与 LCEL 练习")
    parser.add_argument(
        "--mode",
        choices=("summary", "batch", "stream", "all"),
        default="summary",
        help="选择单条、批量、流式或完整流程",
    )
    parser.add_argument("text", nargs="?", help="单条模式和流式模式使用的文本")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    load_dotenv()
    model = create_chat_model(load_settings())
    chain = create_adaptive_summary_chain(model)

    if args.mode in {"summary", "stream", "all"}:
        text = args.text or SHORT_TEXT
        if args.mode in {"summary", "all"}:
            if args.mode == "all":
                print("=== Invoke result ===")
            print(chain.invoke({"text": text}))
        if args.mode in {"stream", "all"}:
            if args.mode == "all":
                print("\n=== Stream result ===")
            for chunk in chain.stream({"text": text}):
                print(chunk, end="", flush=True)
            print()

    if args.mode in {"batch", "all"}:
        results = chain.batch(
            [
                {"text": SHORT_TEXT},
                {"text": LONG_TEXT},
            ]
        )
        if args.mode == "all":
            print("\n=== Batch results ===")
        else:
            print("=== Batch results ===")
        for index, result in enumerate(results, start=1):
            print(f"{index}. {result}")


if __name__ == "__main__":
    main()
