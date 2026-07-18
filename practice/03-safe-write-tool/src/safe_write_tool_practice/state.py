from enum import Enum


class RefundStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class InvalidTransition(ValueError):
    """Raised when a refund state transition is not allowed."""


_TRANSITIONS: dict[tuple[RefundStatus, str], RefundStatus] = {
    (RefundStatus.PENDING_APPROVAL, "APPROVED"): RefundStatus.PROCESSING,
    (RefundStatus.PENDING_APPROVAL, "REJECTED"): RefundStatus.FAILED,
    (RefundStatus.PROCESSING, "PROVIDER_SUCCEEDED"): RefundStatus.SUCCEEDED,
    (RefundStatus.PROCESSING, "PROVIDER_FAILED"): RefundStatus.FAILED,
    (RefundStatus.PROCESSING, "PROVIDER_TIMEOUT"): RefundStatus.UNKNOWN,
    (RefundStatus.UNKNOWN, "RECONCILED_SUCCEEDED"): RefundStatus.SUCCEEDED,
    (RefundStatus.UNKNOWN, "RECONCILED_FAILED"): RefundStatus.FAILED,
}


def transition(status: RefundStatus, event: str) -> RefundStatus:
    try:
        return _TRANSITIONS[(status, event)]
    except KeyError as exc:
        raise InvalidTransition(
            f"不允许从 {status.value} 通过 {event} 转换"
        ) from exc
