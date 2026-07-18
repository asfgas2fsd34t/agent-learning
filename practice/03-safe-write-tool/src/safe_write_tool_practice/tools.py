from decimal import Decimal, InvalidOperation
from typing import Any

from .refunds import ExecutionContext, RefundCommand, RefundService


REFUND_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "request_refund",
        "description": "为指定订单申请退款。这是高风险写操作。",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount": {"type": "number", "exclusiveMinimum": 0},
            },
            "required": ["order_id", "amount"],
            "additionalProperties": False,
        },
    },
}


def execute_refund_tool(
    arguments: dict[str, Any],
    *,
    context: ExecutionContext,
    service: RefundService,
) -> dict[str, Any]:
    try:
        amount = Decimal(str(arguments["amount"]))
        order_id = str(arguments["order_id"]).strip()
    except (KeyError, InvalidOperation, ValueError):
        return {
            "success": False,
            "error_code": "INVALID_ARGUMENTS",
            "message": "退款参数不完整或格式错误",
            "retryable": False,
        }

    if not order_id or not context.idempotency_key:
        return {
            "success": False,
            "error_code": "INVALID_ARGUMENTS",
            "message": "订单号不能为空，且必须由应用程序提供幂等键",
            "retryable": False,
        }

    return service.execute(
        RefundCommand(
            order_id=order_id,
            amount=amount,
            idempotency_key=context.idempotency_key,
        ),
        context,
    )
