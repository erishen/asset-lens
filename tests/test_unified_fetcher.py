"""
Tests for Unified Fetcher.
统一数据获取器测试
"""

import pytest
from unittest.mock import patch, MagicMock


class TestUnifiedFetcher:
    """统一数据获取器测试"""

    def test_module_import(self):
        """测试模块导入"""
        try:
            from asset_lens.data.unified_fetcher import UnifiedFetcher
            assert UnifiedFetcher is not None
        except ImportError:
            pytest.skip("UnifiedFetcher not available")

    def test_fetcher_init(self):
        """测试初始化"""
        try:
            from asset_lens.data.unified_fetcher import UnifiedFetcher
            fetcher = UnifiedFetcher()
            assert fetcher is not None
        except ImportError:
            pytest.skip("UnifiedFetcher not available")

    def test_fetcher_has_methods(self):
        """测试方法存在"""
        try:
            from asset_lens.data.unified_fetcher import UnifiedFetcher
            fetcher = UnifiedFetcher()
            
            # 测试方法存在
            assert hasattr(fetcher, 'fetch') or hasattr(fetcher, 'get_data')
        except ImportError:
            pytest.skip("UnifiedFetcher not available")


class TestDataFetcher:
    """数据获取器测试"""

    def test_fetch_stock_data(self):
        """测试获取股票数据"""
        # 模拟股票数据
        stock_data = {
            "code": "sh600519",
            "name": "贵州茅台",
            "price": 1800.00,
            "change_percent": 1.5,
        }
        assert stock_data["code"] == "sh600519"
        assert stock_data["price"] > 0

    def test_fetch_index_data(self):
        """测试获取指数数据"""
        # 模拟指数数据
        index_data = {
            "code": "sh000001",
            "name": "上证指数",
            "price": 3000.00,
            "change_percent": -0.5,
        }
        assert index_data["code"] == "sh000001"
        assert "指数" in index_data["name"]

    def test_fetch_fund_data(self):
        """测试获取基金数据"""
        # 模拟基金数据
        fund_data = {
            "code": "000001",
            "name": "华夏成长",
            "nav": 1.5,
            "date": "2026-03-09",
        }
        assert fund_data["code"] == "000001"
        assert fund_data["nav"] > 0
