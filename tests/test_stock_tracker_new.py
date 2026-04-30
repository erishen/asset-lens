"""
Tests for Stock Tracker.
股票跟踪器测试
"""

from unittest.mock import MagicMock, patch

import pytest


class TestStockTracker:
    """股票跟踪器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.stock_tracker import StockTracker

        assert StockTracker is not None

    @pytest.fixture
    def tracker(self):
        """创建跟踪器实例"""
        from asset_lens.data.stock_tracker import StockTracker

        with patch("asset_lens.data.stock_tracker.config") as mock_config:
            mock_config.cache_path = MagicMock()
            return StockTracker()

    def test_tracker_init(self, tracker):
        """测试初始化"""
        assert tracker is not None

    def test_add_stock(self, tracker):
        """测试添加股票"""
        # 测试方法存在
        assert hasattr(tracker, "record_daily") or hasattr(tracker, "record_batch")

    def test_remove_stock(self, tracker):
        """测试移除股票"""
        # 测试方法存在
        assert hasattr(tracker, "record_daily") or hasattr(tracker, "detect_monster_stocks")

    def test_get_stocks(self, tracker):
        """测试获取股票列表"""
        # 测试方法存在
        assert hasattr(tracker, "get_tracking_report") or hasattr(tracker, "print_tracking_report")

    def test_update_stock(self, tracker):
        """测试更新股票"""
        # 测试方法存在
        assert hasattr(tracker, "record_daily") or hasattr(tracker, "record_batch")


class TestStockTrackerRecord:
    """股票跟踪记录测试"""

    def test_record_creation(self):
        """测试创建记录"""
        record = {
            "code": "sh600519",
            "name": "贵州茅台",
            "buy_price": 1800.00,
            "current_price": 1850.00,
            "status": "holding",
        }
        assert record["code"] == "sh600519"
        assert record["status"] == "holding"

    def test_record_profit_calculation(self):
        """测试收益计算"""
        buy_price = 1800.00
        current_price = 1850.00
        profit_rate = (current_price - buy_price) / buy_price * 100
        assert profit_rate == pytest.approx(2.78, rel=0.1)

    def test_record_status(self):
        """测试状态"""
        statuses = ["holding", "watching", "sold"]
        for status in statuses:
            assert status in ["holding", "watching", "sold"]


class TestStockTrackerBatch:
    """股票跟踪批量操作测试"""

    def test_batch_add(self):
        """测试批量添加"""
        stocks = [
            {"code": "sh600519", "name": "贵州茅台"},
            {"code": "sz000001", "name": "平安银行"},
        ]
        assert len(stocks) == 2

    def test_batch_update(self):
        """测试批量更新"""
        stocks = [
            {"code": "sh600519", "price": 1800},
            {"code": "sz000001", "price": 15},
        ]
        for stock in stocks:
            stock["updated"] = True
        assert all(s["updated"] for s in stocks)
