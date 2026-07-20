from typing import Any
import unittest

from langchain_core.runnables import RunnableLambda

from langchain_basics.structured import StudyNote, extract_study_note


class FakeStructuredModel:
    def __init__(self) -> None:
        self.schema: type[StudyNote] | None = None
        self.method: str | None = None

    def with_structured_output(
        self,
        schema: type[StudyNote],
        **kwargs: Any,
    ) -> RunnableLambda:
        self.schema = schema
        self.method = kwargs.get("method")
        return RunnableLambda(
            lambda prompt: schema(
                topic="Runnable",
                key_points=["统一接口", "链式组合", "支持测试"],
                summary="Runnable 让 LangChain 组件可以组合执行。",
            )
        )


class StructuredOutputTest(unittest.TestCase):
    def test_returns_validated_pydantic_model(self) -> None:
        model = FakeStructuredModel()

        result = extract_study_note("介绍 Runnable", model)

        self.assertIsInstance(result, StudyNote)
        self.assertEqual(result.topic, "Runnable")
        self.assertEqual(len(result.key_points), 3)
        self.assertIs(model.schema, StudyNote)
        self.assertEqual(model.method, "function_calling")

    def test_rejects_empty_text(self) -> None:
        with self.assertRaisesRegex(ValueError, "不能为空"):
            extract_study_note("", FakeStructuredModel())


if __name__ == "__main__":
    unittest.main()

