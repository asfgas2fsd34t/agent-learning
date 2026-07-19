import unittest

from agent_evaluation.evaluate import EvaluationCase, evaluate_cases


class EvaluationTest(unittest.TestCase):
    def test_calculates_accuracy_and_error_code(self) -> None:
        cases = [
            EvaluationCase(case_id="ok", question="q1", expected_contains="答案"),
            EvaluationCase(case_id="bad", question="q2", expected_contains="正确"),
        ]
        summary = evaluate_cases(cases, lambda question: "这是答案")
        self.assertEqual(summary.total, 2)
        self.assertEqual(summary.passed, 1)
        self.assertEqual(summary.accuracy, 0.5)
        self.assertEqual(summary.cases[1].error_code, "ANSWER_MISMATCH")

    def test_classifies_execution_error(self) -> None:
        summary = evaluate_cases([EvaluationCase(case_id="error", question="q", expected_contains="x")], lambda question: 1 / 0)
        self.assertEqual(summary.cases[0].error_code, "EXECUTION_ERROR")


if __name__ == "__main__":
    unittest.main()

