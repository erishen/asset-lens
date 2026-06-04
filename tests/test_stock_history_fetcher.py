"""
Tests for stock_history_fetcher.py
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.data.stock_history_fetcher import StockHistoryFetcher


class TestStockHistoryFetcher:
    """StockHistoryFetcher 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def fetcher(self, temp_cache_path):
        """创建测试实例"""
        with patch("asset_lens.data.stock_history_fetcher.config") as mock_config:
            mock_config.cache_path = temp_cache_path
            fetcher = StockHistoryFetcher()
            yield fetcher

    def test_init(self, fetcher):
        """测试初始化"""
        assert fetcher.cache_path.exists()

    def test_load_history_cache_no_file(self, fetcher):
        """测试加载缓存历史 - 文件不存在"""
        result = fetcher.load_history_cache()
        assert result == {}

    def test_save_history_cache(self, fetcher):
        """测试保存历史数据"""
        history_data = {"sh600519": {"name": "贵州茅台", "data": [{"date": "2024-01-01", "close": 1800.0}]}}

        fetcher.save_history_cache(history_data)

        # Verify data was saved by loading it back
        loaded = fetcher.load_history_cache()
        assert "sh600519" in loaded

    def test_check_cache_validity_no_file(self, fetcher):
        """测试检查缓存有效性 - 文件不存在"""
        result = fetcher.check_cache_validity()

        assert result["is_valid"] is False

    def test_get_cache_statistics_no_file(self, fetcher):
        """测试获取缓存统计 - 文件不存在"""
        result = fetcher.get_cache_statistics()

        assert result["total"] == 0

    def test_clear_cache(self, fetcher):
        """测试清除缓存"""
        history_data = {"sh600519": {"name": "贵州茅台", "data": []}}
        fetcher.save_history_cache(history_data)

        result = fetcher.clear_cache()

        assert result is True

    def test_baostock_logout(self, fetcher):
        """测试 Baostock 登出"""
        fetcher._baostock_logged_in = True

        mock_bs = MagicMock()
        with patch.dict("sys.modules", {"baostock": mock_bs}):
            fetcher.baostock_logout()

        assert fetcher._baostock_logged_in is False
