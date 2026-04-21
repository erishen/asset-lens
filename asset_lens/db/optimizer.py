"""
Database Optimizer for asset-lens.
数据库优化器 - 索引优化、WAL模式、查询优化
"""

import logging
import sqlite3
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """数据库优化器"""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "asset_lens.db")

        self.db_path = db_path
        self._optimization_log: list[dict[str, Any]] = []

    @contextmanager
    def _get_raw_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """获取原始 SQLite 连接"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def enable_wal_mode(self) -> dict[str, Any]:
        """
        启用 WAL 模式 (Write-Ahead Logging)

        WAL 模式的优势:
        - 读写不阻塞，并发性能提升
        - 更好的崩溃恢复
        - 更快的写入速度

        Returns:
            优化结果
        """
        result = {
            "action": "enable_wal_mode",
            "status": "unknown",
            "before": None,
            "after": None,
            "message": "",
        }

        try:
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("PRAGMA journal_mode;")
                before = cursor.fetchone()[0]
                result["before"] = before

                cursor.execute("PRAGMA journal_mode=WAL;")
                after = cursor.fetchone()[0]
                result["after"] = after

                if after.lower() == "wal":
                    result["status"] = "success"
                    result["message"] = f"WAL 模式已启用 ({before} -> {after})"
                else:
                    result["status"] = "failed"
                    result["message"] = f"WAL 模式启用失败: {after}"

        except Exception as e:
            result["status"] = "error"
            result["message"] = str(e)

        self._optimization_log.append(result)
        return result

    def optimize_pragmas(self) -> dict[str, Any]:
        """
        优化 SQLite PRAGMA 设置

        Returns:
            优化结果
        """
        pragmas = {
            "synchronous": "NORMAL",
            "cache_size": "-64000",
            "temp_store": "MEMORY",
            "mmap_size": "268435456",
            "page_size": "4096",
        }

        result: dict[str, Any] = {
            "action": "optimize_pragmas",
            "status": "success",
            "settings": {},
            "message": "",
        }

        try:
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()

                for pragma, value in pragmas.items():
                    cursor.execute(f"PRAGMA {pragma}={value};")
                    cursor.execute(f"PRAGMA {pragma};")
                    current = cursor.fetchone()[0]
                    result["settings"][pragma] = current

                result["message"] = f"已优化 {len(pragmas)} 个 PRAGMA 设置"

        except Exception as e:
            result["status"] = "error"
            result["message"] = str(e)

        self._optimization_log.append(result)
        return result

    def create_indexes(self, session: Session) -> dict[str, Any]:
        """
        创建优化索引

        Returns:
            优化结果
        """
        indexes = [
            ("idx_kline_code_date_desc", "stock_klines", "code, date DESC"),
            ("idx_kline_close", "stock_klines", "close"),
            ("idx_kline_volume", "stock_klines", "volume"),
            ("idx_kline_change_percent", "stock_klines", "change_percent"),
            ("idx_kline_turnover", "stock_klines", "turnover_rate"),
            ("idx_kline_date_desc", "stock_klines", "date DESC"),
            ("idx_kline_created", "stock_klines", "created_at"),
            ("idx_stock_industry", "stock_info", "industry"),
            ("idx_stock_sector", "stock_info", "sector"),
            ("idx_stock_market", "stock_info", "market"),
            ("idx_pred_date_desc", "prediction_records", "predict_date DESC"),
            ("idx_pred_code_date_desc", "prediction_records", "code, predict_date DESC"),
            ("idx_pred_confidence", "prediction_records", "confidence"),
            ("idx_sync_status", "data_sync_logs", "status"),
            ("idx_sync_start_desc", "data_sync_logs", "sync_start DESC"),
        ]

        result: dict[str, Any] = {
            "action": "create_indexes",
            "status": "success",
            "created": [],
            "skipped": [],
            "failed": [],
            "message": "",
        }

        for idx_name, table, columns in indexes:
            try:
                check_sql = text(
                    f"SELECT name FROM sqlite_master WHERE type='index' AND name='{idx_name}'"
                )
                existing = session.execute(check_sql).fetchone()

                if existing:
                    result["skipped"].append(idx_name)
                else:
                    create_sql = text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({columns})")
                    session.execute(create_sql)
                    session.commit()
                    result["created"].append(idx_name)

            except Exception as e:
                result["failed"].append({"name": idx_name, "error": str(e)})

        result["message"] = (
            f"创建 {len(result['created'])} 个索引, "
            f"跳过 {len(result['skipped'])} 个已存在索引"
        )

        self._optimization_log.append(result)
        return result

    def analyze_tables(self, session: Session) -> dict[str, Any]:
        """
        分析表统计信息 (ANALYZE)

        ANALYZE 会收集统计信息，帮助查询优化器选择更好的执行计划

        Returns:
            优化结果
        """
        result: dict[str, Any] = {
            "action": "analyze_tables",
            "status": "success",
            "tables": [],
            "message": "",
        }

        try:
            tables = [
                "stock_klines",
                "stock_info",
                "ml_models",
                "prediction_records",
                "data_sync_logs",
            ]

            for table in tables:
                try:
                    session.execute(text(f"ANALYZE {table}"))
                    result["tables"].append(table)
                except Exception:
                    pass

            session.commit()
            result["message"] = f"已分析 {len(result['tables'])} 个表"

        except Exception as e:
            result["status"] = "error"
            result["message"] = str(e)

        self._optimization_log.append(result)
        return result

    def vacuum_database(self) -> dict[str, Any]:
        """
        清理数据库碎片 (VACUUM)

        VACUUM 会重建数据库文件，释放未使用的空间

        Returns:
            优化结果
        """
        result: dict[str, Any] = {
            "action": "vacuum",
            "status": "success",
            "before_size": 0,
            "after_size": 0,
            "freed_mb": 0,
            "message": "",
        }

        try:
            db_file = Path(self.db_path.replace("sqlite:///", ""))
            if db_file.exists():
                result["before_size"] = db_file.stat().st_size

            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("VACUUM")

            if db_file.exists():
                result["after_size"] = db_file.stat().st_size
                freed: int = result["before_size"] - result["after_size"]
                result["freed_mb"] = round(freed / 1024 / 1024, 2)

            result["message"] = f"已清理数据库，释放 {result['freed_mb']} MB 空间"

        except Exception as e:
            result["status"] = "error"
            result["message"] = str(e)

        self._optimization_log.append(result)
        return result

    def get_index_usage(self, session: Session) -> list[dict[str, Any]]:
        """
        获取索引使用情况

        Returns:
            索引使用情况列表
        """
        try:
            result = session.execute(
                text(
                    "SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
                )
            )
            indexes = []
            for row in result:
                indexes.append(
                    {
                        "name": row[0],
                        "table": row[1],
                    }
                )
            return indexes
        except Exception:
            return []

    def get_table_stats(self, session: Session) -> dict[str, Any]:
        """
        获取表统计信息

        Returns:
            表统计信息
        """
        stats: dict[str, Any] = {}

        tables = ["stock_klines", "stock_info", "ml_models", "prediction_records", "data_sync_logs"]

        for table in tables:
            try:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                row = result.fetchone()
                count = row[0] if row else 0
                stats[table] = {"row_count": count}
            except Exception:
                stats[table] = {"row_count": 0}

        return stats

    def benchmark_query(self, session: Session, query: str, iterations: int = 3) -> dict[str, Any]:
        """
        基准测试查询性能

        Args:
            session: 数据库会话
            query: SQL 查询
            iterations: 迭代次数

        Returns:
            基准测试结果
        """
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            try:
                session.execute(text(query))
                session.commit()
                elapsed = time.perf_counter() - start
                times.append(elapsed)
            except Exception:
                times.append(-1)

        valid_times = [t for t in times if t > 0]

        return {
            "query": query[:100] + "..." if len(query) > 100 else query,
            "iterations": iterations,
            "avg_time_ms": round(sum(valid_times) / len(valid_times) * 1000, 2) if valid_times else -1,
            "min_time_ms": round(min(valid_times) * 1000, 2) if valid_times else -1,
            "max_time_ms": round(max(valid_times) * 1000, 2) if valid_times else -1,
        }

    def run_full_optimization(self, session: Session) -> dict[str, Any]:
        """
        运行完整优化流程

        Args:
            session: 数据库会话

        Returns:
            优化结果
        """
        results: dict[str, Any] = {
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "optimizations": [],
            "summary": {},
        }

        optimizations: list[dict[str, Any]] = [
            self.enable_wal_mode(),
            self.optimize_pragmas(),
            self.create_indexes(session),
            self.analyze_tables(session),
        ]
        results["optimizations"] = optimizations

        results["summary"] = {
            "total": len(optimizations),
            "success": sum(1 for o in optimizations if o.get("status") == "success"),
            "failed": sum(1 for o in optimizations if o.get("status") == "error"),
        }

        results["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")

        return results

    def get_optimization_log(self) -> list[dict[str, Any]]:
        """获取优化日志"""
        return self._optimization_log


db_optimizer = DatabaseOptimizer()
