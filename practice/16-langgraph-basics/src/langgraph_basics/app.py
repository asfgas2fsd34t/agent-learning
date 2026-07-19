import os
import sys
from typing import Callable, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph


class State(TypedDict, total=False):
    topic: str
    outline: list[str]
    draft: str


def create_model() -> ChatOpenAI:
    options = {"model": os.environ["LLM_MODEL"], "api_key": os.environ["LLM_API_KEY"], "temperature": 0}
    if os.getenv("LLM_BASE_URL"):
        options["base_url"] = os.environ["LLM_BASE_URL"]
    return ChatOpenAI(**options)


def build_graph(writer: Callable[[str], str]) :
    def plan_node(state: State) -> dict[str, object]:
        return {"outline": [f"{state['topic']} 的定义", f"{state['topic']} 的工作流程", f"{state['topic']} 的边界"]}

    def write_node(state: State) -> dict[str, str]:
        outline = "、".join(state["outline"])
        return {"draft": writer(f"主题：{state['topic']}\n提纲：{outline}")}

    builder = StateGraph(State)
    builder.add_node("plan", plan_node)
    builder.add_node("write", write_node)
    builder.add_edge(START, "plan")
    builder.add_edge("plan", "write")
    builder.add_edge("write", END)
    return builder.compile()


def main() -> None:
    load_dotenv()
    topic = " ".join(sys.argv[1:]).strip() or input("主题：").strip()
    model = create_model()
    graph = build_graph(lambda prompt: str(model.invoke(prompt).content))
    print(graph.invoke({"topic": topic})["draft"])


if __name__ == "__main__":
    main()

