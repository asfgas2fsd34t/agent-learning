from decimal import Decimal
import unittest

from safe_write_tool_practice.refunds import (
    ExecutionContext,
    RefundCommand,
    RefundService,
)


class RefundServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = RefundService(approval_threshold=Decimal("1000"))
        self.command = RefundCommand(
            order_id="order_123",
            amount=Decimal("500"),
            idempotency_key="refund_order_123_500",
        )

    def test_rejects_operator_without_permission(self) -> None:
        result = self.service.execute(
            self.command,
            ExecutionContext(can_refund=False),
        )

        self.assertEqual(result["error_code"], "PERMISSION_DENIED")

    def test_large_refund_requires_human_approval(self) -> None:
        command = RefundCommand(
            order_id="order_456",
            amount=Decimal("1500"),
            idempotency_key="refund_order_456_1500",
        )

        result = self.service.execute(
            command,
            ExecutionContext(can_refund=True, human_approved=False),
        )

        self.assertEqual(result["error_code"], "APPROVAL_REQUIRED")

    def test_approved_large_refund_succeeds(self) -> None:
        command = RefundCommand(
            order_id="order_456",
            amount=Decimal("1500"),
            idempotency_key="refund_order_456_1500",
        )

        result = self.service.execute(
            command,
            ExecutionContext(can_refund=True, human_approved=True),
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["status"], "SUCCEEDED")

    def test_repeated_request_returns_original_result(self) -> None:
        context = ExecutionContext(can_refund=True)

        first = self.service.execute(self.command, context)
        second = self.service.execute(self.command, context)

        self.assertIs(first, second)
        self.assertEqual(first["data"]["refund_no"], second["data"]["refund_no"])

    def test_same_key_with_different_request_is_rejected(self) -> None:
        context = ExecutionContext(can_refund=True)
        self.service.execute(self.command, context)
        changed_command = RefundCommand(
            order_id="order_123",
            amount=Decimal("600"),
            idempotency_key=self.command.idempotency_key,
        )

        result = self.service.execute(changed_command, context)

        self.assertEqual(result["error_code"], "IDEMPOTENCY_CONFLICT")

    def test_new_key_cannot_exceed_order_refundable_amount(self) -> None:
        service = RefundService(
            order_amounts={"order_123": Decimal("500")},
        )
        context = ExecutionContext(can_refund=True)
        first = service.execute(self.command, context)
        second_command = RefundCommand(
            order_id="order_123",
            amount=Decimal("500"),
            idempotency_key="another_key_for_order_123",
        )

        second = service.execute(second_command, context)

        self.assertTrue(first["success"])
        self.assertEqual(second["error_code"], "REFUND_LIMIT_EXCEEDED")


if __name__ == "__main__":
    unittest.main()
