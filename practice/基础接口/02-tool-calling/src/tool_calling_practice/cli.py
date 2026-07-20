from collections.abc import Callable

from .agent import answer_question
from .config import Settings, load_settings


def main(
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    settings_loader: Callable[[], Settings] = load_settings,
    answer: Callable[[str, Settings], str] = answer_question,
    load_env: Callable[[], object] | None = None,
) -> None:
    if load_env is None:
        from dotenv import load_dotenv

        load_env = load_dotenv

    load_env()
    settings = settings_loader()
    question = input_fn("请输入你的问题：")
    response = answer(question, settings)
    output_fn(f"\n助手回答：\n{response}")


if __name__ == "__main__":
    main()
