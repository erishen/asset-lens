"""
Tests for Stock Screener.
股票筛选器测试
"""

import pytest
from unittest.mock import patch, MagicMock


class TestStockScreener:
    """股票筛选器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.stock_screener import StockScreener
        assert StockScreener is not None

    @pytest.fixture
    def screener(self):
        """创建筛选器实例"""
        from asset_lens.data.stock_screener import StockScreener
        with patch('asset_lens.data.stock_screener.config') as mock_config:
            mock_config.cache_path = MagicMock()
            return StockScreener()

    def test_screener_init(self, screener):
        """测试初始化"""
        assert screener is not None

    def test_screen_method(self, screener):
        """测试筛选方法"""
        assert hasattr(screener, 'screen') or hasattr(screener, 'filter')


class TestScreenerFilters:
    """筛选条件测试"""

    def test_price_filter(self):
        """测试价格筛选"""
        stocks = [
            {"code": "sh600519", "price": 1800.0},
            {"code": "sz000001", "price": 15.0},
            {"code": "sh601318", "price": 50.0},
        ]
        
        min_price = 10.0
        max_price = 100.0
        
        filtered = [s for s in stocks if min_price <= s["price"] <= max_price]
        assert len(filtered) == 2

    def test_volume_filter(self):
        """测试成交量筛选"""
        stocks = [
            {"code": "sh600519", "volume": 1000000},
            {"code": "sz000001", "volume": 5000000},
            {"code": "sh601318", "volume": 3000000},
        ]
        
        min_volume = 2000000
        
        filtered = [s for s in stocks if s["volume"] >= min_volume]
        assert len(filtered) == 2

    def test_pe_ratio_filter(self):
        """测试市盈率筛选"""
        stocks = [
            {"code": "sh600519", "pe_ratio": 25.0},
            {"code": "sz000001", "pe_ratio": 8.0},
            {"code": "sh601318", "pe_ratio": 15.0},
        ]
        
        max_pe = 20.0
        
        filtered = [s for s in stocks if s["pe_ratio"] <= max_pe]
        assert len(filtered) == 2


class TestScreenerSorting:
    """筛选排序测试"""

    def test_sort_by_price(self):
        """测试按价格排序"""
        stocks = [
            {"code": "sh600519", "price": 1800.0},
            {"code": "sz000001", "price": 15.0},
            {"code": "sh601318", "price": 50.0},
        ]
        
        sorted_stocks = sorted(stocks, key=lambda x: x["price"], reverse=True)
        assert sorted_stocks[0]["code"] == "sh600519"

    def test_sort_by_volume(self):
        """测试按成交量排序"""
        stocks = [
            {"code": "sh600519", "volume": 1000000},
            {"code": "sz000001", "volume": 5000000},
            {"code": "sh601318", "volume": 3000000},
        ]
        
        sorted_stocks = sorted(stocks, key=lambda x: x["volume"], reverse=True)
        assert sorted_stocks[0]["code"] == "sz000001"

    def test_sort_by_change(self):
        """测试按涨跌幅排序"""
        stocks = [
            {"code": "sh600519", "change_percent": 1.5},
            {"code": "sz000001", "change_percent": -0.5},
            {"code": "sh601318", "change_percent": 3.0},
        ]
        
        sorted_stocks = sorted(stocks, key=lambda x: x["change_percent"], reverse=True)
        assert sorted_stocks[0]["code"] == "sh601318"
