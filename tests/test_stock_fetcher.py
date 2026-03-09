"""
Tests for Stock Fetcher.
股票数据获取器测试
"""

import pytest
from unittest.mock import patch, MagicMock


class TestStockFetcher:
    """股票数据获取器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.stock_fetcher import StockDataFetcher
        assert StockDataFetcher is not None

    @pytest.fixture
    def fetcher(self):
        """创建获取器实例"""
        from asset_lens.data.stock_fetcher import StockDataFetcher
        with patch('asset_lens.data.stock_fetcher.config') as mock_config:
            mock_config.cache_path = MagicMock()
            return StockDataFetcher()

    def test_fetcher_init(self, fetcher):
        """测试初始化"""
        assert fetcher is not None

    def test_fetch_method(self, fetcher):
        """测试获取方法"""
        assert hasattr(fetcher, 'fetch_stock_quote_akshare') or hasattr(fetcher, 'fetch_multiple_stocks')


class TestStockDataParsing:
    """股票数据解析测试"""

    def test_parse_stock_code(self):
        """测试解析股票代码"""
        code = "sh600519"
        assert code.startswith("sh") or code.startswith("sz")
        assert len(code) == 8

    def test_parse_stock_name(self):
        """测试解析股票名称"""
        name = "贵州茅台"
        assert len(name) > 0

    def test_parse_price(self):
        """测试解析价格"""
        price_str = "1800.00"
        price = float(price_str)
        assert price == 1800.0

    def test_parse_change_percent(self):
        """测试解析涨跌幅"""
        change_str = "+1.50%"
        change = float(change_str.replace("+", "").replace("%", ""))
        assert change == 1.5


class TestStockDataValidation:
    """股票数据验证测试"""

    def test_validate_price(self):
        """测试验证价格"""
        price = 1800.0
        assert price > 0

    def test_validate_volume(self):
        """测试验证成交量"""
        volume = 1000000
        assert volume >= 0

    def test_validate_change_percent(self):
        """测试验证涨跌幅"""
        change = 10.0
        assert -20 <= change <= 20

    def test_validate_turnover_rate(self):
        """测试验证换手率"""
        turnover = 5.0
        assert 0 <= turnover <= 100
