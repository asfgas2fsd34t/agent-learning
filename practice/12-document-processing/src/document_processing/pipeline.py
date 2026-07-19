from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


ALLOWED_SUFFIXES = {".md", ".txt"}


def load_documents(root: Path) -> list[Document]:
    root = root.resolve()
    documents: list[Document] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        documents.append(
            Document(
                page_content=path.read_text(encoding="utf-8"),
                metadata={"source": path.relative_to(root).as_posix(), "document_id": path.stem},
            )
        )
    return documents


def split_documents(documents: list[Document], chunk_size: int = 200, chunk_overlap: int = 30) -> list[Document]:
    if chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_size 和 chunk_overlap 配置无效")
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(documents)
    counters: dict[str, int] = {}
    for chunk in chunks:
        source = str(chunk.metadata["source"])
        chunk.metadata["chunk_index"] = counters.get(source, 0)
        counters[source] = counters.get(source, 0) + 1
    return chunks

