"""
Tests for stock_pool.py
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.trading.stock_pool import StockPool, StockPoolConfig, StockPosition


class TestStockPosition:
    """StockPosition 测试"""

    def test_default_values(self):
        """测试默认值"""
        pos = StockPosition(
            code="sh600519",
            name="贵州茅台",
            buy_price=1800.0,
            buy_date="2024-01-01",
        )
        assert pos.code == "sh600519"
        assert pos.name == "贵州茅台"
        assert pos.buy_price == 1800.0
        assert pos.buy_date == "2024-01-01"
        assert pos.shares == 100
        assert pos.current_price == 0.0
        assert pos.sell_price is None
        assert pos.sell_date is None
        assert pos.status == "watching"
        assert pos.notes == ""

    def test_custom_values(self):
        """测试自定义值"""
        pos = StockPosition(
            code="sh600519",
            name="贵州茅台",
            buy_price=1800.0,
            buy_date="2024-01-01",
            shares=200,
            current_price=1900.0,
            status="holding",
            notes="测试持仓",
        )
        assert pos.shares == 200
        assert pos.current_price == 1900.0
        assert pos.status == "holding"
        assert pos.notes == "测试持仓"


class TestStockPoolConfig:
    """StockPoolConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = StockPoolConfig()
        assert config.max_pool_size == 50
        assert config.auto_update is True
        assert config.update_interval_days == 1
        assert config.min_score == 60.0
        assert config.strategy_name == "default"

    def test_custom_values(self):
        """测试自定义值"""
        config = StockPoolConfig(
            max_pool_size=100,
            auto_update=False,
            update_interval_days=7,
            min_score=70.0,
            strategy_name="momentum",
        )
        assert config.max_pool_size == 100
        assert config.auto_update is False
        assert config.update_interval_days == 7
        assert config.min_score == 70.0
        assert config.strategy_name == "momentum"


class TestStockPool:
    """StockPool 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def pool(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.trading.stock_pool.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            pool = StockPool("test_pool")
            yield pool

    def test_init(self, pool):
        """测试初始化"""
        assert pool.pool_name == "test_pool"
        assert pool.config is not None
        assert pool.positions == {}

    def test_add_stock_new(self, pool):
        """测试添加新股票"""
        result = pool.add_stock(
            code="sh600519",
            name="贵州茅台",
            price=1800.0,
            status="watching",
            notes="测试添加",
        )

        assert result is True
        assert "sh600519" in pool.positions
        assert pool.positions["sh600519"].name == "贵州茅台"

    def test_add_stock_duplicate_today(self, pool):
        """测试今日重复添加"""
        pool.add_stock("sh600519", "贵州茅台", 1800.0)

        result = pool.add_stock("sh600519", "贵州茅台", 1850.0)

        assert result is False

    def test_add_stock_pool_full(self, pool):
        """测试股票池已满"""
        pool.config.max_pool_size = 1
        pool.add_stock("sh600519", "贵州茅台", 1800.0)

        result = pool.add_stock("sh600000", "浦发银行", 10.0)

        assert result is False

    def test_remove_stock(self, pool):
        """测试移除股票"""
        pool.add_stock("sh600519", "贵州茅台", 1800.0)

        result = pool.remove_stock("sh600519", "测试移除")

        assert result is True
        assert "sh600519" not in pool.positions

    def test_remove_stock_not_exist(self, pool):
        """测试移除不存在的股票"""
        result = pool.remove_stock("sh600519")

        assert result is False

    def test_buy_stock(self, pool):
        """测试买入股票"""
        pool.add_stock("sh600519", "贵州茅台", 1800.0, status="watching")

        result = pool.buy_stock("sh600519", 1800.0, 100)

        assert result is True
        assert pool.positions["sh600519"].status == "holding"
        assert pool.positions["sh600519"].buy_price == 1800.0

    def test_buy_stock_not_in_pool(self, pool):
        """测试买入不在池中的股票"""
        result = pool.buy_stock("sh600519", 1800.0)

        assert result is False

    def test_buy_stock_already_holding(self, pool):
        """测试买入已持有的股票"""
        pool.add_stock("sh600519", "贵州茅台", 1800.0, status="holding")

        result = pool.buy_stock("sh600519", 1800.0)

        assert result is False

    def test_sell_stock(self, pool):
        """测试卖出股票"""
        pool.add_stock("sh600519", "贵州茅台", 1800.0, status="holding")
        pool.positions["sh600519"].buy_price = 1800.0
        pool.positions["sh600519"].shares = 100

        result = pool.sell_stock("sh600519", 1900.0)

        assert result is True
        assert pool.positions["sh600519"].status == "sold"
        assert pool.positions["sh600519"].sell_price == 1900.0

    def test_sell_stock_not_in_pool(self, pool):
        """测试卖出不在池中的股票"""
        result = pool.sell_stock("sh600519", 1900.0)

        assert result is False

    def test_sell_stock_not_holding(self, pool):
        """测试卖出未持有的股票"""
        pool.add_stock("sh600519", "贵州茅台", 1800.0, status="watching")

        result = pool.sell_stock("sh600519", 1900.0)

        assert result is False

    def test_update_prices(self, pool):
        """测试更新价格"""
        pool.add_stock("sh600519", "贵州茅台", 1800.0)

        pool.update_prices({"sh600519": 1850.0})

        assert pool.positions["sh600519"].current_price == 1850.0

    def test_get_performance_empty(self, pool):
        """测试获取绩效 - 空池"""
        result = pool.get_performance()

        assert result["total_stocks"] == 0
        assert result["holding_count"] == 0

    def test_get_performance_with_positions(self, pool):
        """测试获取绩效 - 有持仓"""
        pool.add_stock("sh600519", "贵州茅台", 1800.0, status="holding")
        pool.positions["sh600519"].buy_price = 1800.0
        pool.positions["sh600519"].shares = 100
        pool.positions["sh600519"].current_price = 1900.0

        result = pool.get_performance()

        assert result["total_stocks"] == 1
        assert result["holding_count"] == 1

    def test_list_stocks(self, pool):
        """测试列出股票"""
        pool.add_stock("sh600519", "贵州茅台", 1800.0)
        pool.add_stock("sh600000", "浦发银行", 10.0, status="holding")

        result = pool.list_stocks()

        assert len(result) == 2

    def test_list_stocks_by_status(self, pool):
        """测试按状态列出股票"""
        pool.add_stock("sh600519", "贵州茅台", 1800.0, status="watching")
        pool.add_stock("sh600000", "浦发银行", 10.0, status="holding")

        result = pool.list_stocks("holding")

        assert len(result) == 1
        assert result[0]["code"] == "sh600000"

    def test_save_and_load_pool(self, pool):
        """测试保存和加载股票池"""
        pool.add_stock("sh600519", "贵州茅台", 1800.0)

        new_pool = StockPool("test_pool")
        assert "sh600519" in new_pool.positions

    def test_clear_pool(self, pool):
        """测试清空股票池"""
        pool.add_stock("sh600519", "贵州茅台", 1800.0)

        pool.positions = {}
        pool._save_pool()

        assert len(pool.positions) == 0


class TestStrategyStockPool:
    """策略选股入池测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def pool(self, temp_cache_path):
        """创建股票池实例"""
        with patch('asset_lens.trading.stock_pool.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            from asset_lens.data.stock_pool import StockPool
            pool = StockPool("strategy_test")
            yield pool

    def test_add_stocks_by_strategy(self, pool):
        """测试策略选股入池"""
        stocks = [
            {
                "code": "sh600519",
                "name": "贵州茅台",
                "pe_ratio": 15,
                "market_cap": 200,
                "turnover_rate": 3,
                "change_percent": 2,
            },
            {
                "code": "sz000001",
                "name": "平安银行",
                "pe_ratio": 8,
                "market_cap": 150,
                "turnover_rate": 5,
                "change_percent": 1,
            },
            {
                "code": "sh601318",
                "name": "中国平安",
                "pe_ratio": 50,
                "market_cap": 500,
                "turnover_rate": 20,
                "change_percent": -5,
            },
        ]

        result = pool.add_stocks_by_strategy(
            strategy_name="value",
            stocks=stocks,
            min_score=60.0,
            max_stocks=5,
        )

        assert result["success"] is True
        assert result["strategy"] == "value"
        assert result["added"] > 0
        assert len(result["stocks_added"]) > 0

    def test_add_stocks_by_strategy_with_auto_remove(self, pool):
        """测试策略选股入池 - 自动移除低分"""
        # 先添加一些股票
        pool.add_stock("sh600000", "浦发银行", 10.0, status="watching")

        stocks = [
            {
                "code": "sh600519",
                "name": "贵州茅台",
                "pe_ratio": 15,
                "market_cap": 200,
                "turnover_rate": 3,
                "change_percent": 2,
            },
        ]

        result = pool.add_stocks_by_strategy(
            strategy_name="value",
            stocks=stocks,
            min_score=60.0,
            max_stocks=5,
            auto_remove_low_score=True,
        )

        assert result["success"] is True

    def test_get_strategy_top_stocks(self, pool):
        """测试获取策略评分最高的股票"""
        # 先添加策略选股
        stocks = [
            {
                "code": "sh600519",
                "name": "贵州茅台",
                "pe_ratio": 15,
                "market_cap": 200,
                "turnover_rate": 3,
                "change_percent": 2,
            },
        ]

        pool.add_stocks_by_strategy(
            strategy_name="value",
            stocks=stocks,
            min_score=60.0,
        )

        result = pool.get_strategy_top_stocks("value", top_n=5)

        assert isinstance(result, list)

    def test_clear_strategy_stocks(self, pool):
        """测试清除策略股票"""
        # 先添加策略选股
        stocks = [
            {
                "code": "sh600519",
                "name": "贵州茅台",
                "pe_ratio": 15,
                "market_cap": 200,
                "turnover_rate": 3,
                "change_percent": 2,
            },
        ]

        pool.add_stocks_by_strategy(
            strategy_name="value",
            stocks=stocks,
            min_score=60.0,
        )

        result = pool.clear_strategy_stocks("value")

        assert result["success"] is True
        assert result["strategy"] == "value"

    def test_add_stocks_by_strategy_empty_stocks(self, pool):
        """测试策略选股入池 - 空股票列表"""
        result = pool.add_stocks_by_strategy(
            strategy_name="value",
            stocks=[],
            min_score=60.0,
        )

        assert result["success"] is True
        assert result["added"] == 0

    def test_add_stocks_by_strategy_invalid_strategy(self, pool):
        """测试策略选股入池 - 无效策略"""
        stocks = [
            {
                "code": "sh600519",
                "name": "贵州茅台",
                "pe_ratio": 15,
            },
        ]

        result = pool.add_stocks_by_strategy(
            strategy_name="invalid_strategy",
            stocks=stocks,
            min_score=60.0,
        )

        # 无效策略应该返回成功但添加0只
        assert result["success"] is True
        assert result["added"] == 0
