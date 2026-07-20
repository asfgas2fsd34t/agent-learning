from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict, total=False):
    question: str
    route: str
    context: str
    attempts: int
    answer: str


def build_graph():
    def classify(state: State) -> dict[str, str]:
        route = "knowledge" if any(word in state["question"] for word in ("Runnable", "Tool", "LangChain")) else "direct"
        return {"route": route}

    def retrieve(state: State) -> dict[str, object]:
        attempts = state.get("attempts", 0) + 1
        context = "Runnable 是 LangChain 的统一执行协议。" if "Runnable" in state["question"] else ""
        return {"context": context, "attempts": attempts}

    def rewrite(state: State) -> dict[str, str]:
        return {"question": f"请补充检索：{state['question']}"}

    def answer(state: State) -> dict[str, str]:
        if state.get("route") == "direct":
            return {"answer": "这是一个不需要知识库的直接问题。"}
        if not state.get("context"):
            return {"answer": "知识库没有找到答案。"}
        return {"answer": f"根据知识库：{state['context']}"}

    def after_retrieve(state: State) -> Literal["answer", "rewrite"]:
        if state.get("context") or state.get("attempts", 0) >= 2:
            return "answer"
        return "rewrite"

    builder = StateGraph(State)
    builder.add_node("classify", classify)
    builder.add_node("retrieve", retrieve)
    builder.add_node("rewrite", rewrite)
    builder.add_node("answer", answer)
    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", lambda state: state["route"], {"knowledge": "retrieve", "direct": "answer"})
    builder.add_conditional_edges("retrieve", after_retrieve, {"answer": "answer", "rewrite": "rewrite"})
    builder.add_edge("rewrite", "retrieve")
    builder.add_edge("answer", END)
    return builder.compile()

