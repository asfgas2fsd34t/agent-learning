import os
import sys
import hashlib
import math
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain.tools import tool
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI


class DemoEmbeddings(Embeddings):
    """用于离线学习向量接口的确定性 Embedding，不代表生产语义效果。"""

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * 64
        for index in range(max(1, len(text) - 1)):
            token = text[index:index + 2].lower()
            slot = int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], "big") % len(vector)
            vector[slot] += 1.0
        norm = math.sqrt(sum(item * item for item in vector)) or 1.0
        return [item / norm for item in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def build_store() -> InMemoryVectorStore:
    store = InMemoryVectorStore(DemoEmbeddings())
    store.add_documents([
        Document(page_content="Runnable 支持 invoke、batch、stream 和 ainvoke。", metadata={"source": "runnable.md"}),
        Document(page_content="Tool 是模型可以选择调用的能力。", metadata={"source": "tools.md"}),
    ])
    return store


def retrieve_documents(store: InMemoryVectorStore, query: str) -> tuple[str, list[Document]]:
    documents = store.similarity_search(query, k=2)
    content = "\n\n".join(f"[source={doc.metadata['source']}] {doc.page_content}" for doc in documents)
    return content, documents


def create_retrieval_tool(store: InMemoryVectorStore):
    @tool(response_format="content_and_artifact")
    def retrieve_agent_knowledge(query: str) -> tuple[str, list[Document]]:
        """检索 Agent、Runnable 和 Tool 相关知识。只有问题涉及这些知识时调用。"""
        return retrieve_documents(store, query)
    return retrieve_agent_knowledge


def create_model() -> ChatOpenAI:
    options: dict[str, Any] = {"model": os.environ["LLM_MODEL"], "api_key": os.environ["LLM_API_KEY"], "temperature": 0}
    if os.getenv("LLM_BASE_URL"):
        options["base_url"] = os.environ["LLM_BASE_URL"]
    return ChatOpenAI(**options)


def build_agent(model: Any, store: InMemoryVectorStore):
    retrieval_tool = create_retrieval_tool(store)
    return create_agent(
        model=model,
        tools=[retrieval_tool],
        system_prompt="知识问题需要调用检索工具并引用 source；常识问候不需要检索；知识库没有答案时明确说不知道。",
        middleware=[ToolCallLimitMiddleware(tool_name=retrieval_tool.name, run_limit=2)],
    )


def main() -> None:
    load_dotenv()
    question = " ".join(sys.argv[1:]).strip() or input("问题：").strip()
    result = build_agent(create_model(), build_store()).invoke({"messages": [{"role": "user", "content": question}]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
