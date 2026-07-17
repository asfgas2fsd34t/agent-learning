from collections.abc import Callable

from .chat import ask_model
from .config import Settings, load_settings


def main(
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    settings_loader: Callable[[], Settings] = load_settings,
    ask: Callable[[str, Settings], str] = ask_model,
    load_env: Callable[[], object] | None = None,
) -> None:
    if load_env is None:
        from dotenv import load_dotenv

        load_env = load_dotenv

    load_env()
    settings = settings_loader()
    question = input_fn("请输入你的问题：")
    answer = ask(question, settings)
    output_fn(f"\n模型回答：\n{answer}")


if __name__ == "__main__":
    main()
