"""
Tests for futures_fetcher module.
期货数据获取模块测试
"""

import pytest
from unittest.mock import MagicMock, patch

from asset_lens.data.futures_fetcher import (
    FuturesFetcher,
    get_futures_fetcher,
)


class TestFuturesFetcher:
    """FuturesFetcher 测试"""

    def test_init(self):
        """测试初始化"""
        fetcher = FuturesFetcher()
        assert fetcher._cache == {}
        assert fetcher._akshare is None

    def test_domestic_futures_defined(self):
        """测试国内期货定义"""
        assert "AU0" in FuturesFetcher.DOMESTIC_FUTURES
        assert "CU0" in FuturesFetcher.DOMESTIC_FUTURES
        assert FuturesFetcher.DOMESTIC_FUTURES["AU0"]["name"] == "黄金"

    def test_international_futures_defined(self):
        """测试国际期货定义"""
        assert "XAUUSD" in FuturesFetcher.INTERNATIONAL_FUTURES
        assert "CL" in FuturesFetcher.INTERNATIONAL_FUTURES

    def test_cache_valid(self):
        """测试缓存有效性"""
        fetcher = FuturesFetcher()
        fetcher._cache_time["test"] = 0
        assert not fetcher._is_cache_valid("test")

    def test_clear_cache(self):
        """测试清除缓存"""
        fetcher = FuturesFetcher()
        fetcher._cache["test"] = {"data": "value"}
        fetcher._cache_time["test"] = 100
        fetcher._cache.clear()
        assert "test" not in fetcher._cache


class TestFuturesFetcherWithMock:
    """FuturesFetcher Mock 测试"""

    @patch("asset_lens.data.futures_fetcher.FuturesFetcher.akshare")
    def test_fetch_domestic_quote_success(self, mock_akshare):
        """测试获取国内期货行情成功"""
        fetcher = FuturesFetcher()

        import pandas as pd

        mock_df = pd.DataFrame(
            {
                "symbol": ["AU0", "CU0"],
                "最新价": [450.0, 68000.0],
                "涨跌额": [2.0, 100.0],
                "涨跌幅": [0.45, 0.15],
                "今开": [448.0, 67900.0],
                "最高": [452.0, 68100.0],
                "最低": [447.0, 67800.0],
                "成交量": [100000, 50000],
                "持仓量": [200000, 100000],
                "结算价": [449.5, 67950.0],
                "昨结算": [448.0, 67900.0],
            }
        )
        mock_akshare.futures_main_sina.return_value = mock_df

        result = fetcher.fetch_domestic_quote("AU0")

        assert result is not None
        assert result["symbol"] == "AU0"
        assert result["name"] == "黄金"
        assert result["current_price"] == 450.0

    @patch("asset_lens.data.futures_fetcher.FuturesFetcher.akshare")
    def test_fetch_domestic_quote_not_found(self, mock_akshare):
        """测试获取国内期货行情未找到"""
        fetcher = FuturesFetcher()

        import pandas as pd

        mock_df = pd.DataFrame({"symbol": ["CU0"], "最新价": [68000.0]})
        mock_akshare.futures_main_sina.return_value = mock_df

        result = fetcher.fetch_domestic_quote("AU0")
        assert result is None

    @patch("asset_lens.data.futures_fetcher.FuturesFetcher.akshare")
    def test_fetch_all_domestic_quotes(self, mock_akshare):
        """测试获取所有国内期货行情"""
        fetcher = FuturesFetcher()

        import pandas as pd

        mock_df = pd.DataFrame(
            {
                "symbol": ["AU0", "CU0"],
                "最新价": [450.0, 68000.0],
                "涨跌额": [2.0, 100.0],
                "涨跌幅": [0.45, 0.15],
                "今开": [448.0, 67900.0],
                "最高": [452.0, 68100.0],
                "最低": [447.0, 67800.0],
                "成交量": [100000, 50000],
                "持仓量": [200000, 100000],
            }
        )
        mock_akshare.futures_main_sina.return_value = mock_df

        result = fetcher.fetch_all_domestic_quotes()

        assert len(result) == 2
        assert result[0]["symbol"] == "AU0"


class TestGetFuturesFetcher:
    """get_futures_fetcher 测试"""

    def test_singleton(self):
        """测试单例模式"""
        import asset_lens.data.futures_fetcher as module

        module._futures_fetcher = None

        fetcher1 = get_futures_fetcher()
        fetcher2 = get_futures_fetcher()

        assert fetcher1 is fetcher2
