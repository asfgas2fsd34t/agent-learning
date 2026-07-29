from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class RefundState(TypedDict, total=False):
    order_id: str
    amount: float
    approved: bool
    status: str


def build_graph():
    def validate(state: RefundState) -> dict[str, str]:
        if state["amount"] <= 0:
            return {"status": "invalid_amount"}
        return {"status": "pending_approval"}

    def approval(state: RefundState) -> dict[str, object]:
        decision = interrupt({"action": "refund", "order_id": state["order_id"], "amount": state["amount"]})
        return {"approved": bool(decision)}

    def route(state: RefundState) -> str:
        if state.get("status") == "invalid_amount":
            return "reject"
        return "approval"

    def after_approval(state: RefundState) -> str:
        return "execute" if state.get("approved") else "reject"

    def execute(state: RefundState) -> dict[str, str]:
        return {"status": "completed"}

    def reject(state: RefundState) -> dict[str, str]:
        return {"status": "rejected"}

    builder = StateGraph(RefundState)
    for name, node in [("validate", validate), ("approval", approval), ("execute", execute), ("reject", reject)]:
        builder.add_node(name, node)
    builder.add_edge(START, "validate")
    builder.add_conditional_edges("validate", route, {"approval": "approval", "reject": "reject"})
    builder.add_conditional_edges("approval", after_approval, {"execute": "execute", "reject": "reject"})
    builder.add_edge("execute", END)
    builder.add_edge("reject", END)
    return builder.compile(checkpointer=InMemorySaver())

