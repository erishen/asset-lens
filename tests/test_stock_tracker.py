"""
Tests for stock_tracker.py
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.data.stock_tracker import (
    DailyRecord,
    MonsterStockSignal,
    StockTracker,
    TrackerConfig,
)


class TestDailyRecord:
    """DailyRecord 测试"""

    def test_daily_record_creation(self):
        """测试每日记录创建"""
        record = DailyRecord(
            date="2024-01-01",
            code="sh600519",
            name="贵州茅台",
            open_price=1800.0,
            close_price=1820.0,
            high_price=1830.0,
            low_price=1790.0,
            change_percent=1.5,
            turnover_rate=0.5,
            volume=1000000,
            amount=1800000000,
        )
        assert record.date == "2024-01-01"
        assert record.code == "sh600519"
        assert record.name == "贵州茅台"
        assert record.open_price == 1800.0
        assert record.close_price == 1820.0
        assert record.change_percent == 1.5


class TestMonsterStockSignal:
    """MonsterStockSignal 测试"""

    def test_monster_signal_creation(self):
        """测试妖股信号创建"""
        signal = MonsterStockSignal(
            code="sh600519",
            name="贵州茅台",
            signal_type="limit_up",
            signal_date="2024-01-01",
            description="连续3日涨停",
            score=85.0,
            details={"consecutive_days": 3},
        )
        assert signal.code == "sh600519"
        assert signal.signal_type == "limit_up"
        assert signal.score == 85.0


class TestTrackerConfig:
    """TrackerConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = TrackerConfig()
        assert config.limit_up_threshold == 9.5
        assert config.limit_down_threshold == -9.5
        assert config.consecutive_days == 3
        assert config.volume_surge_ratio == 2.0
        assert config.turnover_surge_ratio == 2.0
        assert config.monster_score_threshold == 70.0

    def test_custom_values(self):
        """测试自定义值"""
        config = TrackerConfig(
            limit_up_threshold=8.0,
            limit_down_threshold=-8.0,
            consecutive_days=5,
            volume_surge_ratio=3.0,
        )
        assert config.limit_up_threshold == 8.0
        assert config.limit_down_threshold == -8.0
        assert config.consecutive_days == 5
        assert config.volume_surge_ratio == 3.0


class TestStockTracker:
    """StockTracker 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def tracker(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.data.stock_tracker.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            tracker = StockTracker("test_pool")
            yield tracker

    def test_init(self, tracker):
        """测试初始化"""
        assert tracker.pool_name == "test_pool"
        assert tracker.tracker_path.exists()
        assert tracker.config is not None

    def test_load_tracker_no_file(self, tracker):
        """测试加载跟踪数据 - 文件不存在"""
        assert tracker.daily_records == {}
        assert tracker.monster_signals == []

    def test_save_tracker(self, tracker):
        """测试保存跟踪数据"""
        tracker.daily_records = {
            "sh600519": [
                DailyRecord(
                    date="2024-01-01",
                    code="sh600519",
                    name="贵州茅台",
                    open_price=1800.0,
                    close_price=1820.0,
                    high_price=1830.0,
                    low_price=1790.0,
                    change_percent=1.5,
                    turnover_rate=0.5,
                    volume=1000000,
                    amount=1800000000,
                )
            ]
        }

        tracker._save_tracker()

        assert tracker.tracker_file.exists()

    def test_record_daily(self, tracker):
        """测试记录每日数据"""
        stock_data = {
            "code": "sh600519",
            "name": "贵州茅台",
            "open": 1800.0,
            "close": 1820.0,
            "high": 1830.0,
            "low": 1790.0,
            "change_percent": 1.5,
            "turnover_rate": 0.5,
            "volume": 1000000,
            "amount": 1800000000,
        }

        result = tracker.record_daily(stock_data)

        assert result is True
        assert "sh600519" in tracker.daily_records

    def test_record_daily_returns_false_for_duplicate(self, tracker):
        """测试记录重复数据返回 False"""
        stock_data = {
            "code": "sh600519",
            "name": "贵州茅台",
            "open": 1800.0,
            "close": 1820.0,
            "high": 1830.0,
            "low": 1790.0,
            "change_percent": 1.5,
            "turnover_rate": 0.5,
            "volume": 1000000,
            "amount": 1800000000,
        }

        # 第一次记录
        result1 = tracker.record_daily(stock_data)
        assert result1 is True

        # 第二次记录同一天（重复）
        result2 = tracker.record_daily(stock_data)
        assert result2 is False

        # 确保只有一条记录
        assert len(tracker.daily_records["sh600519"]) == 1

    def test_record_daily_returns_false_for_empty_code(self, tracker):
        """测试空代码返回 False"""
        stock_data = {
            "code": "",
            "name": "测试",
        }

        result = tracker.record_daily(stock_data)
        assert result is False

    def test_record_batch(self, tracker):
        """测试批量记录"""
        # 先添加股票到股票池
        from asset_lens.trading.stock_pool import StockPool, StockPosition
        from datetime import date
        
        with patch.object(tracker.stock_pool, 'positions', {
            "sh600519": StockPosition(code="sh600519", name="贵州茅台", status="holding", buy_price=1800.0, buy_date=date(2024, 1, 1)),
            "sh600000": StockPosition(code="sh600000", name="浦发银行", status="holding", buy_price=10.0, buy_date=date(2024, 1, 1)),
        }):
            stocks = [
                {
                    "code": "sh600519",
                    "name": "贵州茅台",
                    "open": 1800.0,
                    "close": 1820.0,
                    "high": 1830.0,
                    "low": 1790.0,
                    "change_percent": 1.5,
                    "turnover_rate": 0.5,
                    "volume": 1000000,
                    "amount": 1800000000,
                },
                {
                    "code": "sh600000",
                    "name": "浦发银行",
                    "open": 10.0,
                    "close": 10.2,
                    "high": 10.3,
                    "low": 9.9,
                    "change_percent": 2.0,
                    "turnover_rate": 1.5,
                    "volume": 5000000,
                    "amount": 50000000,
                },
            ]

            result = tracker.record_batch(stocks)

            assert result >= 1

    def test_record_batch_skips_duplicates(self, tracker):
        """测试批量记录跳过重复数据"""
        from asset_lens.trading.stock_pool import StockPosition
        from datetime import date
        
        with patch.object(tracker.stock_pool, 'positions', {
            "sh600519": StockPosition(code="sh600519", name="贵州茅台", status="holding", buy_price=1800.0, buy_date=date(2024, 1, 1)),
        }):
            stocks = [
                {
                    "code": "sh600519",
                    "name": "贵州茅台",
                    "open": 1800.0,
                    "close": 1820.0,
                    "high": 1830.0,
                    "low": 1790.0,
                    "change_percent": 1.5,
                    "turnover_rate": 0.5,
                    "volume": 1000000,
                    "amount": 1800000000,
                },
            ]

            # 第一次批量记录
            result1 = tracker.record_batch(stocks)
            assert result1 == 1

            # 第二次批量记录（重复）
            result2 = tracker.record_batch(stocks)
            assert result2 == 0

            # 确保只有一条记录
            assert len(tracker.daily_records["sh600519"]) == 1

    def test_detect_monster_stocks_empty(self, tracker):
        """测试检测妖股 - 空数据"""
        result = tracker.detect_monster_stocks()

        assert result == []

    def test_get_tracking_report(self, tracker):
        """测试获取跟踪报告"""
        tracker.daily_records = {
            "sh600519": [
                DailyRecord(
                    date="2024-01-01",
                    code="sh600519",
                    name="贵州茅台",
                    open_price=1800.0,
                    close_price=1820.0,
                    high_price=1830.0,
                    low_price=1790.0,
                    change_percent=1.5,
                    turnover_rate=0.5,
                    volume=1000000,
                    amount=1800000000,
                )
            ]
        }

        result = tracker.get_tracking_report()

        assert isinstance(result, dict)
