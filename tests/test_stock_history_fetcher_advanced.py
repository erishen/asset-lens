"""
Additional tests for stock_history_fetcher.py
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from asset_lens.data.stock_history_fetcher import StockHistoryFetcher


class TestStockHistoryFetcherProperties:
    """Tests for lazy-loaded properties"""

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

    def test_tushare_property_no_token(self, fetcher):
        """Test tushare property without token"""
        with patch.dict("os.environ", {}, clear=True):
            # Remove TUSHARE_TOKEN from environment
            import os
            os.environ.pop("TUSHARE_TOKEN", None)
            result = fetcher.tushare
            assert result is None

    def test_baostock_property_import_error(self, fetcher):
        """Test baostock property with import error"""
        fetcher._baostock = None

        with patch("builtins.__import__", side_effect=ImportError("No module")):
            result = fetcher.baostock
            assert result is None


class TestFetchHistoryBaostock:
    """Tests for fetch_history_baostock method"""

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

    def test_fetch_history_baostock_no_module(self, fetcher):
        """Test fetch_history_baostock without baostock module"""
        with patch.dict("sys.modules", {"baostock": None}):
            # Clear cached import in source module
            source_mod = __import__("asset_lens.data.stock_history_sources", fromlist=["stock_history_sources"])
            if hasattr(source_mod, "bs"):
                delattr(source_mod, "bs")
            result = fetcher.fetch_history_baostock("sh600519", 60)
            assert result is None

    def test_fetch_history_baostock_login_failure(self, fetcher):
        """Test fetch_history_baostock with login failure"""
        mock_bs = MagicMock()
        mock_bs.login.return_value = MagicMock(error_code="1", error_msg="Login failed")

        with patch.dict("sys.modules", {"baostock": mock_bs}):
            fetcher._baostock_logged_in = False
            result = fetcher.fetch_history_baostock("sh600519", 60)
            assert result is None

    def test_fetch_history_baostock_login_retry_success(self, fetcher):
        """Test fetch_history_baostock with login success"""
        mock_bs = MagicMock()
        mock_bs.login.return_value = MagicMock(error_code="0")

        mock_rs = MagicMock()
        mock_rs.error_code = "0"
        mock_rs.next.return_value = False
        mock_bs.query_history_k_data_plus.return_value = mock_rs

        with patch.dict("sys.modules", {"baostock": mock_bs}):
            fetcher._baostock_logged_in = False
            result = fetcher.fetch_history_baostock("sh600519", 60)
            # Login succeeds but data is empty
            assert result is None

    def test_fetch_history_baostock_query_error(self, fetcher):
        """Test fetch_history_baostock with query error"""
        mock_bs = MagicMock()
        mock_bs.login.return_value = MagicMock(error_code="0")
        mock_bs.query_history_k_data_plus.return_value = MagicMock(error_code="1")

        with patch.dict("sys.modules", {"baostock": mock_bs}):
            fetcher._baostock_logged_in = False
            result = fetcher.fetch_history_baostock("sh600519", 60)
            assert result is None

    def test_fetch_history_baostock_success(self, fetcher):
        """Test fetch_history_baostock success"""
        mock_bs = MagicMock()
        mock_bs.login.return_value = MagicMock(error_code="0")

        mock_rs = MagicMock()
        mock_rs.error_code = "0"
        mock_rs.next.side_effect = [True, True, False]
        mock_rs.get_row_data.side_effect = [
            ["2024-01-01", "sh.600519", "1800", "1850", "1790", "1820", "1000000", "1800000000", "0.5", "1.5"],
            ["2024-01-02", "sh.600519", "1820", "1870", "1810", "1850", "1200000", "1900000000", "0.6", "1.6"],
        ]
        mock_bs.query_history_k_data_plus.return_value = mock_rs

        with patch.dict("sys.modules", {"baostock": mock_bs}):
            fetcher._baostock_logged_in = False
            result = fetcher.fetch_history_baostock("sh600519", 60)

            assert result is not None
            assert result["code"] == "sh600519"
            assert result["source"] == "baostock"
            assert len(result["klines"]) == 2

    def test_fetch_history_baostock_empty_data(self, fetcher):
        """Test fetch_history_baostock with empty data"""
        mock_bs = MagicMock()
        mock_bs.login.return_value = MagicMock(error_code="0")

        mock_rs = MagicMock()
        mock_rs.error_code = "0"
        mock_rs.next.return_value = False
        mock_bs.query_history_k_data_plus.return_value = mock_rs

        with patch.dict("sys.modules", {"baostock": mock_bs}):
            fetcher._baostock_logged_in = False
            result = fetcher.fetch_history_baostock("sh600519", 60)
            assert result is None

    def test_fetch_history_baostock_exception(self, fetcher):
        """Test fetch_history_baostock with exception"""
        mock_bs = MagicMock()
        mock_bs.login.side_effect = ConnectionError("Network error")

        with patch.dict("sys.modules", {"baostock": mock_bs}):
            fetcher._baostock_logged_in = False
            result = fetcher.fetch_history_baostock("sh600519", 60)
            assert result is None

    def test_fetch_history_baostock_already_logged_in(self, fetcher):
        """Test fetch_history_baostock already logged in"""
        mock_bs = MagicMock()

        mock_rs = MagicMock()
        mock_rs.error_code = "0"
        mock_rs.next.return_value = False
        mock_bs.query_history_k_data_plus.return_value = mock_rs

        with patch.dict("sys.modules", {"baostock": mock_bs}):
            fetcher._baostock_logged_in = True
            fetcher.fetch_history_baostock("sh600519", 60)
            mock_bs.login.assert_not_called()


class TestFetchHistoryTushare:
    """Tests for fetch_history_tushare method"""

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

    def test_fetch_history_tushare_no_module(self, fetcher):
        """Test fetch_history_tushare without tushare module"""
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("TUSHARE_TOKEN", None)
            result = fetcher.fetch_history_tushare("sh600519", 60)
            assert result is None

    def test_fetch_history_tushare_success(self, fetcher):
        """Test fetch_history_tushare success"""
        mock_ts = MagicMock()
        mock_pro = MagicMock()
        mock_df = pd.DataFrame(
            {
                "trade_date": ["20240101", "20240102"],
                "open": [1800, 1820],
                "high": [1850, 1870],
                "low": [1790, 1810],
                "close": [1820, 1850],
                "vol": [1000000, 1200000],
                "amount": [1800000000, 1900000000],
                "pct_chg": [1.0, 1.5],
            }
        )
        mock_pro.daily.return_value = mock_df
        mock_ts.pro_api.return_value = mock_pro

        with patch.dict("sys.modules", {"tushare": mock_ts}):
            with patch.dict("os.environ", {"TUSHARE_TOKEN": "test_token"}):
                result = fetcher.fetch_history_tushare("sh600519", 60)

            assert result is not None
            assert result["code"] == "sh600519"
            assert result["source"] == "tushare"

    def test_fetch_history_tushare_empty_data(self, fetcher):
        """Test fetch_history_tushare with empty data"""
        mock_ts = MagicMock()
        mock_pro = MagicMock()
        mock_df = pd.DataFrame()
        mock_pro.daily.return_value = mock_df
        mock_ts.pro_api.return_value = mock_pro

        with patch.dict("sys.modules", {"tushare": mock_ts}):
            result = fetcher.fetch_history_tushare("sh600519", 60)
            assert result is None

    def test_fetch_history_tushare_exception(self, fetcher):
        """Test fetch_history_tushare with exception"""
        mock_ts = MagicMock()
        mock_ts.pro_api.side_effect = RuntimeError("API error")

        with patch.dict("sys.modules", {"tushare": mock_ts}):
            result = fetcher.fetch_history_tushare("sh600519", 60)
            assert result is None


class TestFetchHistoryAkshare:
    """Tests for fetch_history_akshare method"""

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

    def test_fetch_history_akshare_success(self, fetcher):
        """Test fetch_history_akshare success"""
        mock_ak = MagicMock()
        mock_df = pd.DataFrame(
            {
                "日期": ["2024-01-01", "2024-01-02"],
                "开盘": [1800, 1820],
                "最高": [1850, 1870],
                "最低": [1790, 1810],
                "收盘": [1820, 1850],
                "成交量": [1000000, 1200000],
                "成交额": [1800000000, 1900000000],
                "换手率": [0.5, 0.6],
                "涨跌幅": [1.0, 1.5],
            }
        )
        mock_ak.stock_zh_a_hist.return_value = mock_df

        with patch.object(type(fetcher), "akshare", property(lambda self: mock_ak)):
            result = fetcher.fetch_history_akshare("sh600519", 60)

        assert result is not None
        assert result["code"] == "sh600519"
        assert result["source"] == "akshare"

    def test_fetch_history_akshare_empty_data(self, fetcher):
        """Test fetch_history_akshare with empty data"""
        mock_ak = MagicMock()
        mock_df = pd.DataFrame()
        mock_ak.stock_zh_a_hist.return_value = mock_df

        with patch.object(type(fetcher), "akshare", property(lambda self: mock_ak)):
            result = fetcher.fetch_history_akshare("sh600519", 60)
        assert result is None

    def test_fetch_history_akshare_exception(self, fetcher):
        """Test fetch_history_akshare with exception"""
        mock_ak = MagicMock()
        mock_ak.stock_zh_a_hist.side_effect = RuntimeError("API error")

        with patch.object(type(fetcher), "akshare", property(lambda self: mock_ak)):
            result = fetcher.fetch_history_akshare("sh600519", 60)
        assert result is None


class TestFetchHistory:
    """Tests for fetch_history method"""

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

    def test_fetch_history_with_baostock(self, fetcher):
        """Test fetch_history using baostock"""
        mock_result = {"code": "sh600519", "klines": []}

        with (
            patch.object(fetcher, "load_history_cache", return_value={}),
            patch.object(fetcher, "fetch_history_akshare", return_value=None),
            patch.object(fetcher, "fetch_history_baostock", return_value=mock_result),
        ):
            result = fetcher.fetch_history("sh600519", 60)
            assert result is not None
            assert result["code"] == "sh600519"

    def test_fetch_history_with_tushare(self, fetcher):
        """Test fetch_history using tushare when others fail"""
        mock_result = {"code": "sh600519", "klines": []}

        with (
            patch.object(fetcher, "load_history_cache", return_value={}),
            patch.object(fetcher, "fetch_history_akshare", return_value=None),
            patch.object(fetcher, "fetch_history_baostock", return_value=None),
            patch.object(fetcher, "fetch_history_tushare", return_value=mock_result),
        ):
            result = fetcher.fetch_history("sh600519", 60)
            assert result is not None
            assert result["code"] == "sh600519"

    def test_fetch_history_with_akshare(self, fetcher):
        """Test fetch_history using akshare"""
        mock_result = {"code": "sh600519", "klines": []}

        with (
            patch.object(fetcher, "load_history_cache", return_value={}),
            patch.object(fetcher, "fetch_history_akshare", return_value=mock_result),
        ):
            result = fetcher.fetch_history("sh600519", 60)
            assert result is not None
            assert result["code"] == "sh600519"

    def test_fetch_history_all_fail(self, fetcher):
        """Test fetch_history when all sources fail"""
        with (
            patch.object(fetcher, "load_history_cache", return_value={}),
            patch.object(fetcher, "fetch_history_akshare", return_value=None),
            patch.object(fetcher, "fetch_history_baostock", return_value=None),
            patch.object(fetcher, "fetch_history_tushare", return_value=None),
        ):
            result = fetcher.fetch_history("sh600519", 60)
            assert result is None


class TestCacheOperations:
    """Tests for cache operations"""

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

    def test_load_history_cache_valid_file(self, fetcher):
        """Test loading valid cache file"""
        cache_data = {"update_time": "2024-01-01 12:00:00", "data": {"sh600519": {"name": "贵州茅台", "klines": []}}}
        fetcher._cache.save_file("stock_history.json", cache_data, ttl=86400)

        result = fetcher.load_history_cache()
        assert "sh600519" in result

    def test_check_cache_validity_valid(self, fetcher):
        """Test cache validity check with valid cache"""
        klines = [{"date": f"2024-01-{i:02d}", "close": 1800} for i in range(1, 32)]
        cache_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": {
                "sh600519": {
                    "name": "贵州茅台",
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "klines": klines,
                }
            },
        }
        fetcher._cache.save_file("stock_history.json", cache_data, ttl=86400)

        result = fetcher.check_cache_validity()
        assert result["is_valid"] is True

    def test_check_cache_validity_expired(self, fetcher):
        """Test cache validity check with expired cache"""
        cache_data = {
            "update_time": "2020-01-01 00:00:00",
            "data": {
                "sh600519": {
                    "name": "贵州茅台",
                    "update_time": "2020-01-01 00:00:00",
                    "klines": [{"date": "2020-01-01", "close": 1800}],
                }
            },
        }
        fetcher._cache.save_file("stock_history.json", cache_data, ttl=86400)

        result = fetcher.check_cache_validity()
        assert result["is_valid"] is False

    def test_get_cache_statistics_valid(self, fetcher):
        """Test getting cache statistics with valid cache"""
        cache_data = {
            "update_time": "2024-01-01 12:00:00",
            "data": {
                "sh600519": {"name": "贵州茅台", "klines": [{"date": "2024-01-01"}]},
                "sz000001": {"name": "平安银行", "klines": [{"date": "2024-01-01"}]},
            },
        }
        fetcher._cache.save_file("stock_history.json", cache_data, ttl=86400)

        result = fetcher.get_cache_statistics()

        assert result["total"] == 2

    def test_clear_cache_no_file(self, fetcher):
        """Test clearing cache when file doesn't exist"""
        result = fetcher.clear_cache()
        assert result is False


class TestBaostockLogout:
    """Tests for baostock_logout method"""

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

    def test_baostock_logout_not_logged_in(self, fetcher):
        """Test logout when not logged in - baostock_logout always calls bs.logout()"""
        fetcher._baostock_logged_in = False

        mock_bs = MagicMock()
        with patch.dict("sys.modules", {"baostock": mock_bs}):
            fetcher.baostock_logout()
            # baostock_logout always calls bs.logout() regardless of login state
            mock_bs.logout.assert_called_once()
            assert fetcher._baostock_logged_in is False

    def test_baostock_logout_success(self, fetcher):
        """Test successful logout"""
        mock_bs = MagicMock()

        with patch.dict("sys.modules", {"baostock": mock_bs}):
            fetcher._baostock_logged_in = True
            fetcher.baostock_logout()

            mock_bs.logout.assert_called_once()
            assert fetcher._baostock_logged_in is False


class TestCalculateAvgMetrics:
    """Tests for calculate_avg_metrics method"""

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

    def test_calculate_avg_metrics_empty(self, fetcher):
        """Test calculate_avg_metrics with empty data"""
        result = fetcher.calculate_avg_metrics({"klines": []})
        assert result["avg_turnover_rate"] == 0
        assert result["avg_amount"] == 0
        assert result["avg_volume"] == 0

    def test_calculate_avg_metrics_with_data(self, fetcher):
        """Test calculate_avg_metrics with data"""
        history = {
            "klines": [
                {"turnover_rate": 0.5, "amount": 1000000, "volume": 1000},
                {"turnover_rate": 0.6, "amount": 1200000, "volume": 1200},
            ]
        }
        result = fetcher.calculate_avg_metrics(history)
        assert result["avg_turnover_rate"] == 0.55
        assert result["avg_amount"] == 1100000
        assert result["avg_volume"] == 1100


class TestFetchBatchHistory:
    """Tests for fetch_batch_history method"""

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

    def test_fetch_batch_history(self, fetcher):
        """Test fetch_batch_history"""
        mock_result = {"code": "sh600519", "klines": []}

        with patch.object(fetcher, "fetch_history", return_value=mock_result):
            with patch.object(fetcher, "baostock_logout"):
                result = fetcher.fetch_batch_history(["sh600519"], 60, delay=0)

                assert "sh600519" in result


class TestGetStockRealtimeQuote:
    """Tests for get_stock_realtime_quote method"""

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

    def test_get_stock_realtime_quote_success(self, fetcher):
        """Test get_stock_realtime_quote success"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Tencent stock quote format: fields separated by ~, need at least 40 parts
        # parts[1]=name, [3]=current_price, [4]=prev_close, [5]=open, [6]=volume
        # [32]=change_percent, [33]=high, [34]=low, [37]=amount, [38]=turnover_rate
        parts = [""] * 45
        parts[1] = "贵州茅台"
        parts[3] = "1800.00"
        parts[4] = "1755.00"
        parts[5] = "1790.00"
        parts[6] = "1000000"
        parts[32] = "2.5"
        parts[33] = "1850.00"
        parts[34] = "1790.00"
        parts[37] = "1800000000"
        parts[38] = "0.5"
        mock_response.text = "~".join(parts)

        with patch("requests.get", return_value=mock_response):
            result = fetcher.get_stock_realtime_quote("sh600519")

        assert result is not None
        assert result["code"] == "sh600519"
        assert result["name"] == "贵州茅台"

    def test_get_stock_realtime_quote_not_found(self, fetcher):
        """Test get_stock_realtime_quote not found"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = ""  # No data for this stock

        with patch("requests.get", return_value=mock_response):
            result = fetcher.get_stock_realtime_quote("sh999999")
        # Returns None when stock not found
        assert result is None

    def test_get_stock_realtime_quote_exception(self, fetcher):
        """Test get_stock_realtime_quote with exception"""
        with patch("requests.get", side_effect=ConnectionError("API error")):
            result = fetcher.get_stock_realtime_quote("sh600519")
        assert result is None


class TestGetStocksWithHistory:
    """Tests for get_stocks_with_history method"""

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

    def test_get_stocks_with_history_from_cache(self, fetcher):
        """Test get_stocks_with_history from cache"""
        cache_data = {
            "update_time": "2024-01-01 12:00:00",
            "data": {
                "sh600519": {
                    "name": "贵州茅台",
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "klines": [{"close": 1800, "turnover_rate": 0.5, "amount": 1000000, "volume": 1000, "change_percent": 1.0}],
                    "source": "akshare",
                }
            },
        }
        fetcher._cache.save_file("stock_history.json", cache_data, ttl=86400)

        result = fetcher.get_stocks_with_history(codes=["sh600519"])

        assert len(result) == 1
        assert result[0]["code"] == "sh600519"

    def test_get_stocks_with_history_no_cache(self, fetcher):
        """Test get_stocks_with_history without cache data"""
        # When cache is empty, get_stocks_with_history returns empty list
        result = fetcher.get_stocks_with_history()

        assert isinstance(result, list)
        assert len(result) == 0
