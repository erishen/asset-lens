"""
Tests for Database Module.
数据库模块测试
"""

import tempfile


class TestDatabaseManager:
    """数据库管理器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.db.database import DatabaseManager

        assert DatabaseManager is not None

    def test_init_with_temp_db(self):
        """测试使用临时数据库初始化"""
        from asset_lens.db.database import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            manager = DatabaseManager(db_path)
            assert manager is not None
            assert manager.db_url == db_path
            manager.close()

    def test_get_session(self):
        """测试获取会话"""
        from asset_lens.db.database import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            manager = DatabaseManager(db_path)
            session = manager.get_session()
            assert session is not None
            session.close()
            manager.close()

    def test_save_klines(self):
        """测试保存K线数据"""
        from asset_lens.db.database import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            manager = DatabaseManager(db_path)

            klines = [
                {
                    "date": "2024-01-01",
                    "open": 10.0,
                    "close": 10.5,
                    "high": 11.0,
                    "low": 9.5,
                    "volume": 1000000,
                    "amount": 10500000,
                    "amplitude": 15.0,
                    "change_percent": 5.0,
                    "change_amount": 0.5,
                    "turnover_rate": 2.5,
                },
                {
                    "date": "2024-01-02",
                    "open": 10.5,
                    "close": 11.0,
                    "high": 11.5,
                    "low": 10.0,
                    "volume": 1200000,
                    "amount": 13200000,
                    "amplitude": 14.3,
                    "change_percent": 4.76,
                    "change_amount": 0.5,
                    "turnover_rate": 3.0,
                },
            ]

            count = manager.save_klines("sh600519", klines, "test_source")
            assert count == 2
            manager.close()

    def test_get_klines(self):
        """测试获取K线数据"""
        from asset_lens.db.database import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            manager = DatabaseManager(db_path)

            klines = [
                {
                    "date": "2024-01-01",
                    "open": 10.0,
                    "close": 10.5,
                    "high": 11.0,
                    "low": 9.5,
                    "volume": 1000000,
                    "amount": 10500000,
                },
            ]

            manager.save_klines("sh600519", klines, "test_source")

            result = manager.get_klines("sh600519", limit=30)
            assert result is not None
            assert len(result) >= 1
            manager.close()

    def test_get_statistics(self):
        """测试获取统计信息"""
        from asset_lens.db.database import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            manager = DatabaseManager(db_path)

            stats = manager.get_statistics()
            assert stats is not None
            assert "stock_count" in stats
            assert "kline_count" in stats
            manager.close()

    def test_get_kline_count(self):
        """测试获取K线数量"""
        from asset_lens.db.database import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            manager = DatabaseManager(db_path)

            klines = [
                {
                    "date": "2024-01-01",
                    "open": 10.0,
                    "close": 10.5,
                    "high": 11.0,
                    "low": 9.5,
                    "volume": 1000000,
                    "amount": 10500000,
                },
            ]

            manager.save_klines("sh600519", klines, "test_source")

            count = manager.get_kline_count("sh600519")
            assert count >= 1
            manager.close()

    def test_save_stock_info(self):
        """测试保存股票信息"""
        from asset_lens.db.database import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            manager = DatabaseManager(db_path)

            info = {
                "code": "sh600519",
                "name": "贵州茅台",
                "industry": "白酒",
                "market": "上海",
            }

            result = manager.save_stock_info(info)
            assert result is True
            manager.close()

    def test_get_stock_codes(self):
        """测试获取股票代码列表"""
        from asset_lens.db.database import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            manager = DatabaseManager(db_path)

            klines = [
                {
                    "date": "2024-01-01",
                    "open": 10.0,
                    "close": 10.5,
                    "high": 11.0,
                    "low": 9.5,
                    "volume": 1000000,
                    "amount": 10500000,
                },
            ]

            manager.save_klines("sh600519", klines, "test_source")

            codes = manager.get_stock_codes()
            assert "sh600519" in codes
            manager.close()


class TestDatabaseModels:
    """数据库模型测试"""

    def test_models_import(self):
        """测试模型导入"""
        from asset_lens.db.models import DataSyncLog, MLModel, PredictionRecord, StockInfo, StockKline

        assert StockKline is not None
        assert StockInfo is not None
        assert PredictionRecord is not None
        assert MLModel is not None
        assert DataSyncLog is not None

    def test_stock_kline_creation(self):
        """测试K线模型创建"""
        from asset_lens.db.models import StockKline

        kline = StockKline(
            code="sh600519",
            date="2024-01-01",
            open=10.0,
            close=10.5,
            high=11.0,
            low=9.5,
            volume=1000000,
            amount=10500000,
        )
        assert kline.code == "sh600519"
        assert kline.date == "2024-01-01"
        assert kline.open == 10.0


class TestDatabaseMigration:
    """数据库迁移测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.db.migration import DataMigration

        assert DataMigration is not None

    def test_migration_init(self):
        """测试迁移初始化"""
        from asset_lens.db.migration import DataMigration

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            migration = DataMigration(db_path)
            assert migration is not None


class TestDatabaseIntegration:
    """数据库集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        from asset_lens.db.database import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"sqlite:///{tmpdir}/test.db"
            manager = DatabaseManager(db_path)

            klines = [
                {
                    "date": f"2024-01-{i:02d}",
                    "open": 10.0 + i * 0.1,
                    "close": 10.5 + i * 0.1,
                    "high": 11.0 + i * 0.1,
                    "low": 9.5 + i * 0.1,
                    "volume": 1000000 + i * 10000,
                    "amount": 10500000 + i * 100000,
                }
                for i in range(1, 11)
            ]

            count = manager.save_klines("sh600519", klines, "test_source")
            assert count == 10

            result = manager.get_klines("sh600519", limit=30)
            assert len(result) >= 10

            stats = manager.get_statistics()
            assert stats["stock_count"] >= 1
            assert stats["kline_count"] >= 10

            manager.close()
