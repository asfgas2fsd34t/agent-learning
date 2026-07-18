import unittest

from safe_write_tool_practice.state import (
    InvalidTransition,
    RefundStatus,
    transition,
)


class RefundStateTest(unittest.TestCase):
    def test_approval_moves_request_to_processing(self) -> None:
        self.assertEqual(
            transition(RefundStatus.PENDING_APPROVAL, "APPROVED"),
            RefundStatus.PROCESSING,
        )

    def test_provider_success_moves_processing_to_succeeded(self) -> None:
        self.assertEqual(
            transition(RefundStatus.PROCESSING, "PROVIDER_SUCCEEDED"),
            RefundStatus.SUCCEEDED,
        )

    def test_provider_timeout_moves_to_unknown(self) -> None:
        self.assertEqual(
            transition(RefundStatus.PROCESSING, "PROVIDER_TIMEOUT"),
            RefundStatus.UNKNOWN,
        )

    def test_unknown_can_be_reconciled_to_succeeded(self) -> None:
        self.assertEqual(
            transition(RefundStatus.UNKNOWN, "RECONCILED_SUCCEEDED"),
            RefundStatus.SUCCEEDED,
        )

    def test_terminal_state_cannot_be_reexecuted(self) -> None:
        with self.assertRaises(InvalidTransition):
            transition(RefundStatus.SUCCEEDED, "APPROVED")


if __name__ == "__main__":
    unittest.main()
