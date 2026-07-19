from pathlib import Path
import sqlite3
from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool
    data: Any | None = None
    error_code: str | None = None
    message: str
    retryable: bool = False


def search_documents(query: str, documents: list[str]) -> ToolResult:
    query = query.strip().lower()
    if not query:
        return ToolResult(success=False, error_code="EMPTY_QUERY", message="查询词不能为空")
    matches = [item for item in documents if query in item.lower()]
    return ToolResult(success=True, data=matches[:10], message="搜索完成")


def read_allowed_file(root: Path, relative_path: str) -> ToolResult:
    root = root.resolve()
    candidate = (root / relative_path).resolve()
    if root not in candidate.parents or candidate.suffix not in {".txt", ".md"}:
        return ToolResult(success=False, error_code="FORBIDDEN_PATH", message="文件路径不允许")
    if not candidate.is_file():
        return ToolResult(success=False, error_code="NOT_FOUND", message="文件不存在")
    return ToolResult(success=True, data={"content": candidate.read_text(encoding="utf-8")}, message="读取成功")


def query_order(database: Path, order_id: str, user_id: str) -> ToolResult:
    connection = sqlite3.connect(database)
    try:
        row = connection.execute(
            "SELECT order_id, user_id, amount FROM orders WHERE order_id = ? AND user_id = ?",
            (order_id, user_id),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return ToolResult(success=False, error_code="NOT_FOUND_OR_FORBIDDEN", message="订单不存在或无权限")
    return ToolResult(success=True, data={"order_id": row[0], "user_id": row[1], "amount": row[2]}, message="查询成功")
