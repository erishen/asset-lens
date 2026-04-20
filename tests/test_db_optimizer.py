"""
Tests for Database Optimizer.
数据库优化器测试
"""

import pytest
import tempfile
from unittest.mock import patch, MagicMock


class TestDatabaseOptimizer:
    """数据库优化器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.db.optimizer import DatabaseOptimizer
        assert DatabaseOptimizer is not None

    def test_init_with_temp_db(self):
        """测试使用临时数据库初始化"""
        from asset_lens.db.optimizer import DatabaseOptimizer

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"
            optimizer = DatabaseOptimizer(db_path)
            assert optimizer is not None
            assert optimizer.db_path == db_path

    def test_enable_wal_mode(self):
        """测试启用 WAL 模式"""
        from asset_lens.db.optimizer import DatabaseOptimizer
        import sqlite3

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"
            optimizer = DatabaseOptimizer(db_path)

            result = optimizer.enable_wal_mode()

            assert result["status"] == "success"
            assert result["after"] == "wal"

    def test_optimize_pragmas(self):
        """测试优化 PRAGMA 设置"""
        from asset_lens.db.optimizer import DatabaseOptimizer

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"
            optimizer = DatabaseOptimizer(db_path)

            result = optimizer.optimize_pragmas()

            assert result["status"] == "success"
            assert "settings" in result
            assert len(result["settings"]) > 0

    def test_create_indexes(self):
        """测试创建索引"""
        from asset_lens.db.optimizer import DatabaseOptimizer
        from asset_lens.db.database import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            manager = DatabaseManager(db_path)
            session = manager.get_session()

            db_file_path = f"{tmpdir}/test.db"
            optimizer = DatabaseOptimizer(db_file_path)

            result = optimizer.create_indexes(session)

            assert result["status"] == "success"
            assert len(result["created"]) > 0

            session.close()
            manager.close()

    def test_analyze_tables(self):
        """测试分析表"""
        from asset_lens.db.optimizer import DatabaseOptimizer
        from asset_lens.db.database import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            manager = DatabaseManager(db_path)
            session = manager.get_session()

            db_file_path = f"{tmpdir}/test.db"
            optimizer = DatabaseOptimizer(db_file_path)

            result = optimizer.analyze_tables(session)

            assert result["status"] == "success"
            assert len(result["tables"]) > 0

            session.close()
            manager.close()

    def test_get_index_usage(self):
        """测试获取索引使用情况"""
        from asset_lens.db.optimizer import DatabaseOptimizer
        from asset_lens.db.database import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            manager = DatabaseManager(db_path)
            session = manager.get_session()

            db_file_path = f"{tmpdir}/test.db"
            optimizer = DatabaseOptimizer(db_file_path)

            optimizer.create_indexes(session)
            indexes = optimizer.get_index_usage(session)

            assert isinstance(indexes, list)

            session.close()
            manager.close()

    def test_get_table_stats(self):
        """测试获取表统计信息"""
        from asset_lens.db.optimizer import DatabaseOptimizer
        from asset_lens.db.database import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            manager = DatabaseManager(db_path)
            session = manager.get_session()

            db_file_path = f"{tmpdir}/test.db"
            optimizer = DatabaseOptimizer(db_file_path)

            stats = optimizer.get_table_stats(session)

            assert isinstance(stats, dict)
            assert "stock_klines" in stats

            session.close()
            manager.close()

    def test_benchmark_query(self):
        """测试基准查询"""
        from asset_lens.db.optimizer import DatabaseOptimizer
        from asset_lens.db.database import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            manager = DatabaseManager(db_path)
            session = manager.get_session()

            db_file_path = f"{tmpdir}/test.db"
            optimizer = DatabaseOptimizer(db_file_path)

            result = optimizer.benchmark_query(session, "SELECT 1", iterations=3)

            assert "avg_time_ms" in result
            assert result["iterations"] == 3

            session.close()
            manager.close()

    def test_run_full_optimization(self):
        """测试完整优化流程"""
        from asset_lens.db.optimizer import DatabaseOptimizer
        from asset_lens.db.database import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            manager = DatabaseManager(db_path)
            session = manager.get_session()

            db_file_path = f"{tmpdir}/test.db"
            optimizer = DatabaseOptimizer(db_file_path)

            result = optimizer.run_full_optimization(session)

            assert "optimizations" in result
            assert "summary" in result
            assert result["summary"]["total"] > 0

            session.close()
            manager.close()

    def test_get_optimization_log(self):
        """测试获取优化日志"""
        from asset_lens.db.optimizer import DatabaseOptimizer

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"
            optimizer = DatabaseOptimizer(db_path)

            optimizer.enable_wal_mode()
            log = optimizer.get_optimization_log()

            assert isinstance(log, list)
            assert len(log) > 0
