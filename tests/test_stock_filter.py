"""
Tests for stock_filter.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from asset_lens.strategy.stock_filter import StockFilter, StockFilterConfig


class TestStockFilterConfig:
    """StockFilterConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = StockFilterConfig()
        assert config.price_min is None
        assert config.price_max is None
        assert config.market_cap_min is None
        assert config.exclude_etf is True
        assert config.sort_key == "turnover_rate"
        assert config.sort_direction == "desc"
        assert config.max_results == 50

    def test_custom_values(self):
        """测试自定义值"""
        config = StockFilterConfig(
            price_min=10.0,
            price_max=100.0,
            market_cap_min=50.0,
            market_cap_max=500.0,
            exclude_etf=False,
            sort_key="market_cap",
            sort_direction="asc",
            max_results=100,
        )
        assert config.price_min == 10.0
        assert config.price_max == 100.0
        assert config.market_cap_min == 50.0
        assert config.market_cap_max == 500.0
        assert config.exclude_etf is False
        assert config.sort_key == "market_cap"
        assert config.sort_direction == "asc"
        assert config.max_results == 100

    def test_exclude_keywords_default(self):
        """测试排除关键词默认值"""
        config = StockFilterConfig()
        assert "ETF" in config.exclude_keywords
        assert "基金" in config.exclude_keywords


class TestStockFilter:
    """StockFilter 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def stock_filter(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.strategy.stock_filter.config') as mock_config:
            mock_config.project_root = temp_cache_path
            stock_filter = StockFilter()
            yield stock_filter

    def test_init(self, stock_filter):
        """测试初始化"""
        assert stock_filter.filter_config is not None

    def test_filter_stock_basic(self, stock_filter):
        """测试基本股票筛选"""
        stock = {
            "name": "贵州茅台",
            "current_price": 1800.0,
            "market_cap": 2000,
            "turnover_rate": 0.5,
            "change_percent": 1.5,
            "volume": 1000000,
            "amplitude": 2.0,
        }

        result = stock_filter.filter_stock(stock)

        assert result is True

    def test_filter_stock_exclude_etf(self, stock_filter):
        """测试排除 ETF"""
        stock = {
            "name": "沪深300ETF",
            "current_price": 5.0,
        }

        result = stock_filter.filter_stock(stock)

        assert result is False

    def test_filter_stock_exclude_fund(self, stock_filter):
        """测试排除基金"""
        stock = {
            "name": "某基金A",
            "current_price": 1.0,
        }

        result = stock_filter.filter_stock(stock)

        assert result is False

    def test_filter_stock_price_range(self, stock_filter):
        """测试价格范围筛选"""
        stock_filter.filter_config.price_min = 10.0
        stock_filter.filter_config.price_max = 100.0

        stock_low = {"name": "低价股", "current_price": 5.0}
        stock_mid = {"name": "正常股", "current_price": 50.0}
        stock_high = {"name": "高价股", "current_price": 200.0}

        assert stock_filter.filter_stock(stock_low) is False
        assert stock_filter.filter_stock(stock_mid) is True
        assert stock_filter.filter_stock(stock_high) is False

    def test_filter_stock_market_cap_range(self, stock_filter):
        """测试市值范围筛选"""
        stock_filter.filter_config.market_cap_min = 50.0
        stock_filter.filter_config.market_cap_max = 500.0

        stock_small = {"name": "小盘股", "current_price": 10.0, "market_cap": 30.0}
        stock_mid = {"name": "中盘股", "current_price": 10.0, "market_cap": 100.0}
        stock_large = {"name": "大盘股", "current_price": 10.0, "market_cap": 1000.0}

        assert stock_filter.filter_stock(stock_small) is False
        assert stock_filter.filter_stock(stock_mid) is True
        assert stock_filter.filter_stock(stock_large) is False

    def test_filter_stock_turnover_rate(self, stock_filter):
        """测试换手率筛选"""
        stock_filter.filter_config.turnover_rate_min = 1.0
        stock_filter.filter_config.turnover_rate_max = 10.0

        stock_low = {"name": "低换手", "current_price": 10.0, "turnover_rate": 0.5}
        stock_mid = {"name": "正常换手", "current_price": 10.0, "turnover_rate": 5.0}
        stock_high = {"name": "高换手", "current_price": 10.0, "turnover_rate": 15.0}

        assert stock_filter.filter_stock(stock_low) is False
        assert stock_filter.filter_stock(stock_mid) is True
        assert stock_filter.filter_stock(stock_high) is False

    def test_filter_stock_change_percent(self, stock_filter):
        """测试涨跌幅筛选"""
        stock_filter.filter_config.change_percent_min = -5.0
        stock_filter.filter_config.change_percent_max = 10.0

        stock_down = {"name": "大跌股", "current_price": 10.0, "change_percent": -8.0}
        stock_normal = {"name": "正常股", "current_price": 10.0, "change_percent": 3.0}
        stock_up = {"name": "大涨股", "current_price": 10.0, "change_percent": 15.0}

        assert stock_filter.filter_stock(stock_down) is False
        assert stock_filter.filter_stock(stock_normal) is True
        assert stock_filter.filter_stock(stock_up) is False

    def test_filter_stock_volume(self, stock_filter):
        """测试成交量筛选"""
        stock_filter.filter_config.volume_min = 1000000
        stock_filter.filter_config.volume_max = 10000000

        stock_low = {"name": "低量股", "current_price": 10.0, "volume": 500000}
        stock_mid = {"name": "正常量股", "current_price": 10.0, "volume": 5000000}
        stock_high = {"name": "高量股", "current_price": 10.0, "volume": 20000000}

        assert stock_filter.filter_stock(stock_low) is False
        assert stock_filter.filter_stock(stock_mid) is True
        assert stock_filter.filter_stock(stock_high) is False

    def test_filter_stocks_batch(self, stock_filter):
        """测试批量筛选股票"""
        stocks = [
            {"name": "贵州茅台", "current_price": 1800.0, "turnover_rate": 0.5},
            {"name": "沪深300ETF", "current_price": 5.0, "turnover_rate": 2.0},
            {"name": "浦发银行", "current_price": 10.0, "turnover_rate": 1.5},
        ]

        result = stock_filter.filter_stocks(stocks)

        assert len(result) == 2
        assert all("ETF" not in s["name"] for s in result)

    def test_filter_stocks_sort(self, stock_filter):
        """测试股票排序"""
        stock_filter.filter_config.sort_key = "turnover_rate"
        stock_filter.filter_config.sort_direction = "desc"

        stocks = [
            {"name": "股票A", "current_price": 10.0, "turnover_rate": 1.0},
            {"name": "股票B", "current_price": 10.0, "turnover_rate": 3.0},
            {"name": "股票C", "current_price": 10.0, "turnover_rate": 2.0},
        ]

        result = stock_filter.filter_stocks(stocks)

        assert result[0]["turnover_rate"] == 3.0
        assert result[1]["turnover_rate"] == 2.0
        assert result[2]["turnover_rate"] == 1.0

    def test_filter_stocks_max_results(self, stock_filter):
        """测试最大结果数"""
        stock_filter.filter_config.max_results = 2

        stocks = [
            {"name": "股票A", "current_price": 10.0, "turnover_rate": 1.0},
            {"name": "股票B", "current_price": 10.0, "turnover_rate": 2.0},
            {"name": "股票C", "current_price": 10.0, "turnover_rate": 3.0},
        ]

        result = stock_filter.filter_stocks(stocks)

        assert len(result) == 2

    def test_get_filter_summary(self, stock_filter):
        """测试获取筛选条件摘要"""
        stock_filter.filter_config.price_min = 10.0
        stock_filter.filter_config.price_max = 100.0

        summary = stock_filter.get_filter_summary()

        assert "股票筛选条件" in summary
        assert "价格范围" in summary

    def test_load_config_with_file(self, stock_filter, temp_cache_path):
        """测试从文件加载配置"""
        config_dir = temp_cache_path / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "stock_filter.json"

        config_data = {
            "filters": {
                "price": {"enabled": True, "min": 5.0, "max": 50.0},
                "market_cap": {"enabled": True, "min": 20.0, "max": 200.0},
            },
            "exclude": {"etf": True, "keywords": ["ETF", "ST"]},
            "sort": {"key": "market_cap", "direction": "asc"},
            "limit": {"max_results": 30},
        }

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        new_filter = StockFilter(config_file)

        assert new_filter.filter_config.price_min == 5.0
        assert new_filter.filter_config.price_max == 50.0
        assert new_filter.filter_config.market_cap_min == 20.0
        assert new_filter.filter_config.sort_key == "market_cap"
        assert new_filter.filter_config.max_results == 30
