from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class RefundCommand:
    order_id: str
    amount: Decimal
    idempotency_key: str


@dataclass(frozen=True)
class ExecutionContext:
    can_refund: bool
    human_approved: bool = False
    idempotency_key: str = ""


class RefundService:
    def __init__(
        self,
        approval_threshold: Decimal = Decimal("1000"),
        order_amounts: dict[str, Decimal] | None = None,
    ) -> None:
        self.approval_threshold = approval_threshold
        self.order_amounts = order_amounts
        self._completed: dict[str, tuple[RefundCommand, dict[str, Any]]] = {}
        self._refunded_totals: dict[str, Decimal] = {}
        self._next_refund_number = 1

    def execute(
        self,
        command: RefundCommand,
        context: ExecutionContext,
    ) -> dict[str, Any]:
        if not context.can_refund:
            return self._error(
                "PERMISSION_DENIED",
                "当前操作者没有退款权限",
            )

        if command.amount <= 0:
            return self._error("INVALID_AMOUNT", "退款金额必须大于 0")

        existing = self._completed.get(command.idempotency_key)
        if existing is not None:
            previous_command, previous_result = existing
            if previous_command != command:
                return self._error(
                    "IDEMPOTENCY_CONFLICT",
                    "同一个幂等键不能用于不同退款请求",
                )
            return previous_result

        if self.order_amounts is not None:
            order_amount = self.order_amounts.get(command.order_id)
            if order_amount is None:
                return self._error("ORDER_NOT_FOUND", "订单不存在")

            refunded_total = self._refunded_totals.get(command.order_id, Decimal("0"))
            if refunded_total + command.amount > order_amount:
                return self._error(
                    "REFUND_LIMIT_EXCEEDED",
                    "累计退款金额不能超过订单金额",
                )

        if command.amount > self.approval_threshold and not context.human_approved:
            return self._error(
                "APPROVAL_REQUIRED",
                "退款金额超过自动执行上限，需要人工审批",
            )

        result: dict[str, Any] = {
            "success": True,
            "data": {
                "refund_no": f"refund_{self._next_refund_number:04d}",
                "order_id": command.order_id,
                "amount": str(command.amount),
                "status": "SUCCEEDED",
            },
        }
        self._next_refund_number += 1
        self._completed[command.idempotency_key] = (command, result)
        self._refunded_totals[command.order_id] = (
            self._refunded_totals.get(command.order_id, Decimal("0"))
            + command.amount
        )
        return result

    @staticmethod
    def _error(error_code: str, message: str) -> dict[str, Any]:
        return {
            "success": False,
            "error_code": error_code,
            "message": message,
            "retryable": False,
        }
