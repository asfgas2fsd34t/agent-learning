from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from production_tools.tools import query_order, read_allowed_file, search_documents


class ProductionToolsTest(unittest.TestCase):
    def test_search_limits_results(self) -> None:
        result = search_documents("agent", ["Agent 基础", "Python", "Agent 工具"])
        self.assertEqual(result.data, ["Agent 基础", "Agent 工具"])

    def test_file_reader_blocks_path_traversal(self) -> None:
        with TemporaryDirectory() as directory:
            result = read_allowed_file(Path(directory), "../secret.txt")
            self.assertEqual(result.error_code, "FORBIDDEN_PATH")

    def test_order_query_enforces_user_scope(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "orders.db"
            connection = sqlite3.connect(database)
            connection.execute("CREATE TABLE orders(order_id TEXT, user_id TEXT, amount REAL)")
            connection.execute("INSERT INTO orders VALUES (?, ?, ?)", ("order_1", "user_1", 99.0))
            connection.commit()
            connection.close()
            allowed = query_order(database, "order_1", "user_1")
            denied = query_order(database, "order_1", "user_2")
            self.assertTrue(allowed.success)
            self.assertEqual(denied.error_code, "NOT_FOUND_OR_FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
