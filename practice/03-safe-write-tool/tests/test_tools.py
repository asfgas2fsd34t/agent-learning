import unittest

from safe_write_tool_practice.refunds import ExecutionContext, RefundService
from safe_write_tool_practice.tools import execute_refund_tool


class RefundToolTest(unittest.TestCase):
    def test_human_approval_is_not_a_model_argument(self) -> None:
        service = RefundService()
        result = execute_refund_tool(
            {
                "order_id": "order_789",
                "amount": 2000,
                "idempotency_key": "model_must_not_control_this",
                "human_approved": True,
            },
            context=ExecutionContext(
                can_refund=True,
                human_approved=False,
                idempotency_key="request_789",
            ),
            service=service,
        )

        self.assertEqual(result["error_code"], "APPROVAL_REQUIRED")

    def test_application_context_provides_idempotency_key(self) -> None:
        service = RefundService()
        context = ExecutionContext(
            can_refund=True,
            idempotency_key="request_789",
        )
        arguments = {
            "order_id": "order_789",
            "amount": 500,
        }

        first = execute_refund_tool(arguments, context=context, service=service)
        second = execute_refund_tool(arguments, context=context, service=service)

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
