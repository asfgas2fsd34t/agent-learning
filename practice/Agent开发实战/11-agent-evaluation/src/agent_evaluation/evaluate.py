from dataclasses import dataclass
import time
from typing import Callable

from pydantic import BaseModel


class EvaluationCase(BaseModel):
    case_id: str
    question: str
    expected_contains: str


class CaseResult(BaseModel):
    case_id: str
    passed: bool
    latency_ms: float
    error_code: str | None = None


class EvaluationSummary(BaseModel):
    total: int
    passed: int
    accuracy: float
    average_latency_ms: float
    cases: list[CaseResult]


def evaluate_cases(cases: list[EvaluationCase], answer: Callable[[str], str]) -> EvaluationSummary:
    results: list[CaseResult] = []
    for case in cases:
        started = time.perf_counter()
        try:
            output = answer(case.question)
            passed = case.expected_contains in output
            error_code = None if passed else "ANSWER_MISMATCH"
        except Exception:
            passed = False
            error_code = "EXECUTION_ERROR"
        elapsed = (time.perf_counter() - started) * 1000
        results.append(CaseResult(case_id=case.case_id, passed=passed, latency_ms=elapsed, error_code=error_code))
    total = len(results)
    passed = sum(item.passed for item in results)
    return EvaluationSummary(total=total, passed=passed, accuracy=passed / total if total else 0.0, average_latency_ms=sum(item.latency_ms for item in results) / total if total else 0.0, cases=results)


CASES = [
    EvaluationCase(case_id="runnable", question="Runnable 是什么？", expected_contains="统一"),
    EvaluationCase(case_id="tool", question="Tool 是什么？", expected_contains="工具"),
]


def main() -> None:
    summary = evaluate_cases(CASES, lambda question: "Runnable 是统一执行协议，Tool 是模型可以选择调用的工具。")
    print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

