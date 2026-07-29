import argparse
import uuid

from dotenv import load_dotenv

from langsmith_practice.tracing import invoke_observed


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="LangSmith 可观测性练习")
    parser.add_argument("question", nargs="?", default="什么是 Agent？")
    parser.add_argument("--environment", default="local")
    args = parser.parse_args()

    print(
        invoke_observed(
            args.question,
            request_id=str(uuid.uuid4()),
            environment=args.environment,
        )
    )


if __name__ == "__main__":
    main()
