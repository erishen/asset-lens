"""
Tests for stock_fetcher.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.data.stock_fetcher import StockDataFetcher


class TestStockDataFetcher:
    """StockDataFetcher 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def fetcher(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.data.stock_fetcher.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            mock_config.project_root = temp_cache_path
            mock_config.finnhub_api_key = "demo"
            fetcher = StockDataFetcher()
            yield fetcher

    def test_init(self, fetcher):
        """测试初始化"""
        assert fetcher.cache_path.exists()
        assert fetcher.stock_cache_file is not None

    def test_load_stock_codes_config_no_file(self, fetcher):
        """测试加载股票代码配置 - 文件不存在"""
        result = fetcher._load_stock_codes_config()

        assert result == {}

    def test_load_stock_codes_config_with_file(self, fetcher):
        """测试加载股票代码配置 - 有文件"""
        config_dir = fetcher.cache_path / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "fund_stock_codes.json"

        config_data = {
            "stocks": [
                {"name": "贵州茅台", "code": "sh600519", "keywords": ["茅台"]},
                {"name": "腾讯控股", "code": "hk00700"},
            ]
        }

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        with patch('asset_lens.data.stock_fetcher.config') as mock_config:
            mock_config.project_root = fetcher.cache_path
            fetcher._stock_codes_map = None
            result = fetcher._load_stock_codes_config()

            assert "贵州茅台" in result
            assert result["贵州茅台"] == "sh600519"

    def test_fetch_stock_quote_akshare_invalid_code(self, fetcher):
        """测试获取无效代码行情"""
        result = fetcher.fetch_stock_quote_akshare("invalid")

        assert result is None

    def test_fetch_us_stock_quote(self, fetcher):
        """测试获取美股行情"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "c": 180.0,
            "pc": 178.0,
            "h": 182.0,
            "l": 177.0,
            "o": 179.0,
        }

        with patch('requests.get', return_value=mock_response):
            result = fetcher.fetch_us_stock_quote("AAPL")

            assert result is not None
            assert result["code"] == "AAPL"
            assert result["current_price"] == 180.0

    def test_fetch_us_stock_quote_no_data(self, fetcher):
        """测试获取美股行情 - 无数据"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"c": 0, "pc": 0}

        with patch('requests.get', return_value=mock_response):
            result = fetcher.fetch_us_stock_quote("INVALID")

            assert result is None

    def test_fetch_multiple_stocks(self, fetcher):
        """测试批量获取股票行情"""
        with patch.object(fetcher, 'fetch_stock_quote_akshare') as mock_fetch:
            mock_fetch.return_value = {
                "code": "sh600519",
                "name": "贵州茅台",
                "current_price": 1800.0,
                "change_percent": 1.12,
            }

            result = fetcher.fetch_multiple_stocks(["sh600519"])

            assert "data" in result
            assert "sh600519" in result["data"]

    def test_get_cached_stocks_no_cache(self, fetcher):
        """测试获取缓存股票 - 无缓存"""
        result = fetcher.get_cached_stocks()

        assert result == {}

    def test_get_cached_stocks_with_cache(self, fetcher):
        """测试获取缓存股票 - 有缓存"""
        cache_data = {
            "update_time": "2024-01-01 12:00:00",
            "data": {"sh600519": {"name": "贵州茅台"}},
        }

        with open(fetcher.stock_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        result = fetcher.get_cached_stocks()

        assert "data" in result
        assert "sh600519" in result["data"]
