"""
Additional tests for stock_history_fetcher.py
"""

import json
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
        fetcher._tushare_token = ""
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
        fetcher._baostock = None

        with patch.object(type(fetcher), "baostock", property(lambda self: None)):
            result = fetcher.fetch_history_baostock("sh600519", 60)
            assert result is None

    def test_fetch_history_baostock_login_failure(self, fetcher):
        """Test fetch_history_baostock with login failure (all retries)"""
        mock_bs = MagicMock()
        mock_bs.login.return_value = MagicMock(error_code="1", error_msg="Login failed")

        fetcher._baostock = mock_bs
        fetcher._baostock_logged_in = False
        fetcher._baostock_failed = False

        result = fetcher.fetch_history_baostock("sh600519", 60)
        assert result is None
        # BAOSTOCK_MAX_RETRIES = 2，所以尝试 2 次
        assert mock_bs.login.call_count == 2

    def test_fetch_history_baostock_login_retry_success(self, fetcher):
        """Test fetch_history_baostock with login retry success"""
        mock_bs = MagicMock()
        # 第一次失败，第二次成功
        mock_bs.login.side_effect = [
            MagicMock(error_code="1", error_msg="Login failed"),
            MagicMock(error_code="0"),
        ]

        mock_rs = MagicMock()
        mock_rs.error_code = "0"
        mock_rs.next.return_value = False
        mock_bs.query_history_k_data_plus.return_value = mock_rs

        fetcher._baostock = mock_bs
        fetcher._baostock_logged_in = False

        result = fetcher.fetch_history_baostock("sh600519", 60)
        # 第二次登录成功，但数据为空
        assert result is None
        assert mock_bs.login.call_count == 2

    def test_fetch_history_baostock_query_error(self, fetcher):
        """Test fetch_history_baostock with query error"""
        mock_bs = MagicMock()
        mock_bs.login.return_value = MagicMock(error_code="0")
        mock_bs.query_history_k_data_plus.return_value = MagicMock(error_code="1")

        fetcher._baostock = mock_bs
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
            ["2024-01-01", "sh.600519", "1800", "1850", "1790", "1820", "1000000", "1800000000", "0.5"],
            ["2024-01-02", "sh.600519", "1820", "1870", "1810", "1850", "1200000", "1900000000", "0.6"],
        ]
        mock_bs.query_history_k_data_plus.return_value = mock_rs

        fetcher._baostock = mock_bs
        fetcher._baostock_logged_in = False

        result = fetcher.fetch_history_baostock("sh600519", 60)

        assert result is not None
        assert result["code"] == "sh600519"
        assert result["data_source"] == "Baostock"
        assert len(result["klines"]) == 2

    def test_fetch_history_baostock_empty_data(self, fetcher):
        """Test fetch_history_baostock with empty data"""
        mock_bs = MagicMock()
        mock_bs.login.return_value = MagicMock(error_code="0")

        mock_rs = MagicMock()
        mock_rs.error_code = "0"
        mock_rs.next.return_value = False
        mock_bs.query_history_k_data_plus.return_value = mock_rs

        fetcher._baostock = mock_bs
        fetcher._baostock_logged_in = False

        result = fetcher.fetch_history_baostock("sh600519", 60)
        assert result is None

    def test_fetch_history_baostock_exception(self, fetcher):
        """Test fetch_history_baostock with exception"""
        mock_bs = MagicMock()
        mock_bs.login.side_effect = Exception("Network error")

        fetcher._baostock = mock_bs
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

        fetcher._baostock = mock_bs
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
        with patch.object(type(fetcher), "tushare", property(lambda self: None)):
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
            }
        )
        mock_pro.daily.return_value = mock_df
        mock_ts.pro_api.return_value = mock_pro

        fetcher._tushare = mock_ts
        fetcher._tushare_token = "test_token"

        result = fetcher.fetch_history_tushare("sh600519", 60)

        assert result is not None
        assert result["code"] == "sh600519"
        assert result["data_source"] == "Tushare"

    def test_fetch_history_tushare_empty_data(self, fetcher):
        """Test fetch_history_tushare with empty data"""
        mock_ts = MagicMock()
        mock_pro = MagicMock()
        mock_df = pd.DataFrame()
        mock_pro.daily.return_value = mock_df
        mock_ts.pro_api.return_value = mock_pro

        fetcher._tushare = mock_ts
        fetcher._tushare_token = "test_token"

        result = fetcher.fetch_history_tushare("sh600519", 60)
        assert result is None

    def test_fetch_history_tushare_exception(self, fetcher):
        """Test fetch_history_tushare with exception"""
        mock_ts = MagicMock()
        mock_ts.pro_api.side_effect = Exception("API error")

        fetcher._tushare = mock_ts
        fetcher._tushare_token = "test_token"

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
                "date": ["2024-01-01", "2024-01-02"],
                "open": [1800, 1820],
                "high": [1850, 1870],
                "low": [1790, 1810],
                "close": [1820, 1850],
                "amount": [1000000, 1200000],
            }
        )
        mock_ak.stock_zh_a_hist_tx.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.fetch_history_akshare("sh600519", 60)

        assert result is not None
        assert result["code"] == "sh600519"
        assert result["data_source"] == "AkShare-腾讯"

    def test_fetch_history_akshare_empty_data(self, fetcher):
        """Test fetch_history_akshare with empty data"""
        mock_ak = MagicMock()
        mock_df = pd.DataFrame()
        mock_ak.stock_zh_a_hist_tx.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.fetch_history_akshare("sh600519", 60)
        assert result is None

    def test_fetch_history_akshare_exception(self, fetcher):
        """Test fetch_history_akshare with exception"""
        mock_ak = MagicMock()
        mock_ak.stock_zh_a_hist_tx.side_effect = Exception("API error")

        fetcher._akshare = mock_ak

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
            patch.object(fetcher, "_tushare_token", None),
            patch.object(fetcher, "fetch_history_akshare_daily", return_value=None),
            patch.object(fetcher, "fetch_history_baostock", return_value=mock_result),
        ):
            result = fetcher.fetch_history("sh600519", 60)
            assert result == mock_result

    def test_fetch_history_with_tushare(self, fetcher):
        """Test fetch_history using tushare when baostock fails"""
        mock_result = {"code": "sh600519", "klines": []}

        with (
            patch.object(fetcher, "_tushare_token", "test_token"),
            patch.object(fetcher, "fetch_history_tushare", return_value=mock_result),
        ):
            result = fetcher.fetch_history("sh600519", 60)
            assert result == mock_result

    def test_fetch_history_with_akshare(self, fetcher):
        """Test fetch_history using akshare when others fail"""
        mock_result = {"code": "sh600519", "klines": []}

        with (
            patch.object(fetcher, "_tushare_token", None),
            patch.object(fetcher, "fetch_history_akshare_daily", return_value=None),
            patch.object(fetcher, "fetch_history_baostock", return_value=None),
            patch.object(fetcher, "fetch_history_akshare", return_value=mock_result),
        ):
            result = fetcher.fetch_history("sh600519", 60)
            assert result == mock_result

    def test_fetch_history_all_fail(self, fetcher):
        """Test fetch_history when all sources fail"""
        with (
            patch.object(fetcher, "_tushare_token", None),
            patch.object(fetcher, "fetch_history_akshare_daily", return_value=None),
            patch.object(fetcher, "fetch_history_baostock", return_value=None),
            patch.object(fetcher, "fetch_history_akshare", return_value=None),
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
        with open(fetcher.history_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

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
                    "klines": klines,
                }
            },
        }
        with open(fetcher.history_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        result = fetcher.check_cache_validity()
        assert result["valid"] is True

    def test_check_cache_validity_expired(self, fetcher):
        """Test cache validity check with expired cache"""
        cache_data = {
            "update_time": "2020-01-01 00:00:00",
            "data": {
                "sh600519": {
                    "name": "贵州茅台",
                    "klines": [{"date": "2020-01-01", "close": 1800}],
                }
            },
        }
        with open(fetcher.history_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        result = fetcher.check_cache_validity()
        assert result["valid"] is False

    def test_get_cache_statistics_valid(self, fetcher):
        """Test getting cache statistics with valid cache"""
        cache_data = {
            "update_time": "2024-01-01 12:00:00",
            "data": {
                "sh600519": {"name": "贵州茅台", "klines": [{"date": "2024-01-01"}]},
                "sz000001": {"name": "平安银行", "klines": [{"date": "2024-01-01"}]},
            },
        }
        with open(fetcher.history_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        result = fetcher.get_cache_statistics()

        assert result["exists"] is True
        assert result["total_stocks"] == 2

    def test_clear_cache_no_file(self, fetcher):
        """Test clearing cache when file doesn't exist"""
        result = fetcher.clear_cache()
        assert result is True


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
        """Test logout when not logged in"""
        fetcher._baostock_logged_in = False
        fetcher._baostock = MagicMock()

        fetcher.baostock_logout()

        fetcher._baostock.logout.assert_not_called()

    def test_baostock_logout_success(self, fetcher):
        """Test successful logout"""
        mock_bs = MagicMock()

        fetcher._baostock = mock_bs
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
        mock_ak = MagicMock()
        mock_df = pd.DataFrame(
            {
                "代码": ["600519"],
                "名称": ["贵州茅台"],
                "最新价": [1800],
                "涨跌幅": [2.5],
                "涨跌额": [45],
                "成交量": [1000000],
                "成交额": [1800000000],
                "振幅": [3.0],
                "最高": [1850],
                "最低": [1790],
                "今开": [1805],
                "昨收": [1755],
                "换手率": [0.5],
                "市盈率-动态": [30],
                "市净率": [10],
                "总市值": [2000000000000],
            }
        )
        mock_ak.stock_zh_a_spot_em.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.get_stock_realtime_quote("sh600519")

        assert result is not None
        assert result["code"] == "sh600519"
        assert result["name"] == "贵州茅台"

    def test_get_stock_realtime_quote_not_found(self, fetcher):
        """Test get_stock_realtime_quote not found"""
        mock_ak = MagicMock()
        mock_df = pd.DataFrame(
            {
                "代码": ["000001"],
                "名称": ["平安银行"],
            }
        )
        mock_ak.stock_zh_a_spot_em.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.get_stock_realtime_quote("sh600519")
        assert result is None

    def test_get_stock_realtime_quote_exception(self, fetcher):
        """Test get_stock_realtime_quote with exception"""
        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.side_effect = Exception("API error")

        fetcher._akshare = mock_ak

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
                    "klines": [{"turnover_rate": 0.5, "amount": 1000000, "volume": 1000}],
                    "data_source": "AkShare",
                }
            },
        }
        with open(fetcher.history_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        stocks = [{"code": "sh600519", "name": "贵州茅台"}]
        result = fetcher.get_stocks_with_history(stocks, use_cache=True)

        assert len(result) == 1
        assert result[0]["code"] == "sh600519"

    def test_get_stocks_with_history_no_cache(self, fetcher):
        """Test get_stocks_with_history without cache"""
        mock_history = {
            "klines": [{"turnover_rate": 0.5, "amount": 1000000, "volume": 1000}],
            "data_source": "AkShare",
        }

        with patch.object(fetcher, "fetch_history", return_value=mock_history):
            with patch.object(fetcher, "baostock_logout"):
                stocks = [{"code": "sh600519", "name": "贵州茅台"}]
                result = fetcher.get_stocks_with_history(stocks, use_cache=False, delay=0)

                assert len(result) == 1
