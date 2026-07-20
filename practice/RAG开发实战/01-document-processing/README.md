# 练习 12：文档加载与切分

加载 `.md/.txt` 为 `Document`，使用 `RecursiveCharacterTextSplitter` 切分并补充 chunk 元数据。

```powershell
python -m uv sync --all-packages --no-editable
cd practice/RAG开发实战/01-document-processing
python -m uv run python -m unittest discover -s tests -v
```

对应笔记：[02 RAG 技术实现](../../../notes/RAG开发实战/02-RAG技术实现.md)
