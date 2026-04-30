"""
Tests for international_stock_fetcher.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from asset_lens.data.international_stock_fetcher import InternationalStockFetcher


class TestInternationalStockFetcherInit:
    """Tests for initialization"""

    def test_init(self):
        """Test initialization"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)

            with patch("asset_lens.data.international_stock_fetcher.config") as mock_config:
                mock_config.cache_path = temp_path
                fetcher = InternationalStockFetcher()

                assert fetcher.cache_path == temp_path
                assert fetcher.hk_stock_cache == temp_path / "hk_stocks.json"
                assert fetcher.us_stock_cache == temp_path / "us_stocks.json"


class TestFetchHkStockQuote:
    """Tests for fetch_hk_stock_quote method"""

    @pytest.fixture
    def fetcher(self):
        """创建测试实例"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            with patch("asset_lens.data.international_stock_fetcher.config") as mock_config:
                mock_config.cache_path = temp_path
                fetcher = InternationalStockFetcher()
                yield fetcher

    def test_fetch_hk_stock_quote_success(self, fetcher):
        """Test fetch_hk_stock_quote success"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Global Quote": {
                "01. symbol": "00700",
                "02. open": "348.0",
                "03. high": "355.0",
                "04. low": "345.0",
                "05. price": "350.0",
                "08. previous close": "341.5",
                "09. change": "8.5",
                "10. change percent": "2.5%",
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            result = fetcher.fetch_hk_stock_quote("00700")

            assert result is not None
            assert result["code"] == "00700"
            assert result["market"] == "HK"

    def test_fetch_hk_stock_quote_not_found(self, fetcher):
        """Test fetch_hk_stock_quote not found"""
        mock_df = pd.DataFrame(
            {
                "代码": ["00700"],
                "名称": ["腾讯控股"],
            }
        )

        mock_ak = MagicMock()
        mock_ak.stock_hk_spot_em.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.fetch_hk_stock_quote("99999")
            assert result is None

    def test_fetch_hk_stock_quote_empty_data(self, fetcher):
        """Test fetch_hk_stock_quote with empty data"""
        mock_df = pd.DataFrame()

        mock_ak = MagicMock()
        mock_ak.stock_hk_spot_em.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.fetch_hk_stock_quote("00700")
            assert result is None

    def test_fetch_hk_stock_quote_exception(self, fetcher):
        """Test fetch_hk_stock_quote with exception"""
        mock_ak = MagicMock()
        mock_ak.stock_hk_spot_em.side_effect = Exception("API error")

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.fetch_hk_stock_quote("00700")
            assert result is None


class TestFetchUsStockQuote:
    """Tests for fetch_us_stock_quote method"""

    @pytest.fixture
    def fetcher(self):
        """创建测试实例"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            with patch("asset_lens.data.international_stock_fetcher.config") as mock_config:
                mock_config.cache_path = temp_path
                fetcher = InternationalStockFetcher()
                yield fetcher

    def test_fetch_us_stock_quote_success(self, fetcher):
        """Test fetch_us_stock_quote success"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Global Quote": {
                "01. symbol": "AAPL",
                "02. open": "179.0",
                "03. high": "182.0",
                "04. low": "178.0",
                "05. price": "180.0",
                "08. previous close": "177.3",
                "09. change": "2.7",
                "10. change percent": "1.5%",
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            result = fetcher.fetch_us_stock_quote("AAPL")

            assert result is not None
            assert result["code"] == "AAPL"
            assert result["market"] == "US"

    def test_fetch_us_stock_quote_not_found(self, fetcher):
        """Test fetch_us_stock_quote not found"""
        mock_df = pd.DataFrame(
            {
                "代码": ["AAPL"],
                "名称": ["苹果"],
            }
        )

        mock_ak = MagicMock()
        mock_ak.stock_us_spot_em.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.fetch_us_stock_quote("NOTEXIST")
            assert result is None

    def test_fetch_us_stock_quote_exception(self, fetcher):
        """Test fetch_us_stock_quote with exception"""
        mock_ak = MagicMock()
        mock_ak.stock_us_spot_em.side_effect = Exception("API error")

        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("AlphaVantage API error")

            with patch.dict("sys.modules", {"akshare": mock_ak}):
                result = fetcher.fetch_us_stock_quote("AAPL")
                assert result is None


class TestFetchHkStockHistory:
    """Tests for fetch_hk_stock_history method"""

    @pytest.fixture
    def fetcher(self):
        """创建测试实例"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            with patch("asset_lens.data.international_stock_fetcher.config") as mock_config:
                mock_config.cache_path = temp_path
                fetcher = InternationalStockFetcher()
                yield fetcher

    def test_fetch_hk_stock_history_success(self, fetcher):
        """Test fetch_hk_stock_history success"""
        mock_df = pd.DataFrame(
            {
                "日期": ["2024-01-01", "2024-01-02"],
                "开盘": [350.0, 352.0],
                "收盘": [355.0, 358.0],
                "最高": [358.0, 360.0],
                "最低": [348.0, 350.0],
                "成交量": [10000000, 12000000],
            }
        )

        mock_ak = MagicMock()
        mock_ak.stock_hk_daily.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.fetch_hk_stock_history("00700", 60)

            assert result is not None
            assert result["code"] == "00700"
            assert result["market"] == "HK"
            assert len(result["klines"]) == 2

    def test_fetch_hk_stock_history_empty_data(self, fetcher):
        """Test fetch_hk_stock_history with empty data"""
        mock_df = pd.DataFrame()

        mock_ak = MagicMock()
        mock_ak.stock_hk_daily.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.fetch_hk_stock_history("00700", 60)
            assert result is None

    def test_fetch_hk_stock_history_exception(self, fetcher):
        """Test fetch_hk_stock_history with exception"""
        mock_ak = MagicMock()
        mock_ak.stock_hk_daily.side_effect = Exception("API error")

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.fetch_hk_stock_history("00700", 60)
            assert result is None


class TestFetchUsStockHistory:
    """Tests for fetch_us_stock_history method"""

    @pytest.fixture
    def fetcher(self):
        """创建测试实例"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            with patch("asset_lens.data.international_stock_fetcher.config") as mock_config:
                mock_config.cache_path = temp_path
                fetcher = InternationalStockFetcher()
                yield fetcher

    def test_fetch_us_stock_history_success(self, fetcher):
        """Test fetch_us_stock_history success"""
        mock_df = pd.DataFrame(
            {
                "日期": ["2024-01-01", "2024-01-02"],
                "开盘": [180.0, 182.0],
                "收盘": [182.0, 184.0],
                "最高": [183.0, 185.0],
                "最低": [179.0, 181.0],
                "成交量": [50000000, 55000000],
            }
        )

        mock_ak = MagicMock()
        mock_ak.stock_us_daily.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.fetch_us_stock_history("AAPL", 60)

            assert result is not None
            assert result["code"] == "AAPL"
            assert result["market"] == "US"
            assert len(result["klines"]) == 2

    def test_fetch_us_stock_history_empty_data(self, fetcher):
        """Test fetch_us_stock_history with empty data"""
        mock_df = pd.DataFrame()

        mock_ak = MagicMock()
        mock_ak.stock_us_daily.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.fetch_us_stock_history("AAPL", 60)
            assert result is None

    def test_fetch_us_stock_history_exception(self, fetcher):
        """Test fetch_us_stock_history with exception"""
        mock_ak = MagicMock()
        mock_ak.stock_us_daily.side_effect = Exception("API error")

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.fetch_us_stock_history("AAPL", 60)
            assert result is None


class TestSearchHkStock:
    """Tests for search_hk_stock method"""

    @pytest.fixture
    def fetcher(self):
        """创建测试实例"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            with patch("asset_lens.data.international_stock_fetcher.config") as mock_config:
                mock_config.cache_path = temp_path
                fetcher = InternationalStockFetcher()
                yield fetcher

    def test_search_hk_stock_success(self, fetcher):
        """Test search_hk_stock success"""
        mock_df = pd.DataFrame(
            {
                "代码": ["00700", "09988"],
                "名称": ["腾讯控股", "阿里巴巴"],
            }
        )

        mock_ak = MagicMock()
        mock_ak.stock_hk_spot_em.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.search_hk_stock("腾讯")

            assert len(result) == 1
            assert result[0]["code"] == "00700"

    def test_search_hk_stock_by_code(self, fetcher):
        """Test search_hk_stock by code"""
        mock_df = pd.DataFrame(
            {
                "代码": ["00700", "09988"],
                "名称": ["腾讯控股", "阿里巴巴"],
            }
        )

        mock_ak = MagicMock()
        mock_ak.stock_hk_spot_em.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.search_hk_stock("00700")

            assert len(result) == 1
            assert result[0]["code"] == "00700"

    def test_search_hk_stock_empty_result(self, fetcher):
        """Test search_hk_stock with empty result"""
        mock_df = pd.DataFrame(
            {
                "代码": ["00700"],
                "名称": ["腾讯控股"],
            }
        )

        mock_ak = MagicMock()
        mock_ak.stock_hk_spot_em.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.search_hk_stock("NOTEXIST")
            assert len(result) == 0

    def test_search_hk_stock_exception(self, fetcher):
        """Test search_hk_stock with exception"""
        mock_ak = MagicMock()
        mock_ak.stock_hk_spot_em.side_effect = Exception("API error")

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.search_hk_stock("腾讯")
            assert result == []


class TestSearchUsStock:
    """Tests for search_us_stock method"""

    @pytest.fixture
    def fetcher(self):
        """创建测试实例"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            with patch("asset_lens.data.international_stock_fetcher.config") as mock_config:
                mock_config.cache_path = temp_path
                fetcher = InternationalStockFetcher()
                yield fetcher

    def test_search_us_stock_success(self, fetcher):
        """Test search_us_stock success"""
        mock_df = pd.DataFrame(
            {
                "代码": ["AAPL", "GOOGL"],
                "名称": ["苹果", "谷歌"],
            }
        )

        mock_ak = MagicMock()
        mock_ak.stock_us_spot_em.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.search_us_stock("AAPL")

            assert len(result) == 1
            assert result[0]["code"] == "AAPL"

    def test_search_us_stock_exception(self, fetcher):
        """Test search_us_stock with exception"""
        mock_ak = MagicMock()
        mock_ak.stock_us_spot_em.side_effect = Exception("API error")

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.search_us_stock("AAPL")
            assert result == []


class TestGetHkStockList:
    """Tests for get_hk_stock_list method"""

    @pytest.fixture
    def fetcher(self):
        """创建测试实例"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            with patch("asset_lens.data.international_stock_fetcher.config") as mock_config:
                mock_config.cache_path = temp_path
                fetcher = InternationalStockFetcher()
                yield fetcher

    def test_get_hk_stock_list_success(self, fetcher):
        """Test get_hk_stock_list success"""
        mock_df = pd.DataFrame(
            {
                "代码": ["00700", "09988"],
                "名称": ["腾讯控股", "阿里巴巴"],
                "最新价": [350.0, 80.0],
                "涨跌幅": [2.5, 1.5],
                "成交量": [10000000, 5000000],
                "成交额": [3500000000, 400000000],
            }
        )

        mock_ak = MagicMock()
        mock_ak.stock_hk_spot_em.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.get_hk_stock_list()

            assert len(result) == 2
            assert result[0]["code"] == "00700"

    def test_get_hk_stock_list_empty(self, fetcher):
        """Test get_hk_stock_list with empty data"""
        mock_df = pd.DataFrame()

        mock_ak = MagicMock()
        mock_ak.stock_hk_spot_em.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.get_hk_stock_list()
            assert result == []

    def test_get_hk_stock_list_exception(self, fetcher):
        """Test get_hk_stock_list with exception"""
        mock_ak = MagicMock()
        mock_ak.stock_hk_spot_em.side_effect = Exception("API error")

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.get_hk_stock_list()
            assert result == []


class TestGetUsStockList:
    """Tests for get_us_stock_list method"""

    @pytest.fixture
    def fetcher(self):
        """创建测试实例"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            with patch("asset_lens.data.international_stock_fetcher.config") as mock_config:
                mock_config.cache_path = temp_path
                fetcher = InternationalStockFetcher()
                yield fetcher

    def test_get_us_stock_list_success(self, fetcher):
        """Test get_us_stock_list success"""
        mock_df = pd.DataFrame(
            {
                "代码": ["AAPL", "GOOGL"],
                "名称": ["苹果", "谷歌"],
                "最新价": [180.0, 140.0],
                "涨跌幅": [1.5, 2.0],
                "成交量": [50000000, 10000000],
                "成交额": [9000000000, 1400000000],
            }
        )

        mock_ak = MagicMock()
        mock_ak.stock_us_spot_em.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.get_us_stock_list()

            assert len(result) == 2
            assert result[0]["code"] == "AAPL"

    def test_get_us_stock_list_exception(self, fetcher):
        """Test get_us_stock_list with exception"""
        mock_ak = MagicMock()
        mock_ak.stock_us_spot_em.side_effect = Exception("API error")

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.get_us_stock_list()
            assert result == []


class TestCacheOperations:
    """Tests for cache operations"""

    @pytest.fixture
    def fetcher(self):
        """创建测试实例"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            with patch("asset_lens.data.international_stock_fetcher.config") as mock_config:
                mock_config.cache_path = temp_path
                fetcher = InternationalStockFetcher()
                yield fetcher

    def test_save_hk_stocks_cache(self, fetcher):
        """Test save_hk_stocks_cache"""
        stocks = [{"code": "00700", "name": "腾讯控股"}]
        fetcher.save_hk_stocks_cache(stocks)

        assert fetcher.hk_stock_cache.exists()
        with open(fetcher.hk_stock_cache, encoding="utf-8") as f:
            data = json.load(f)
            assert len(data["data"]) == 1

    def test_load_hk_stocks_cache(self, fetcher):
        """Test load_hk_stocks_cache"""
        stocks = [{"code": "00700", "name": "腾讯控股"}]
        fetcher.save_hk_stocks_cache(stocks)

        result = fetcher.load_hk_stocks_cache()
        assert len(result) == 1

    def test_load_hk_stocks_cache_empty(self, fetcher):
        """Test load_hk_stocks_cache with no file"""
        result = fetcher.load_hk_stocks_cache()
        assert result == []

    def test_save_us_stocks_cache(self, fetcher):
        """Test save_us_stocks_cache"""
        stocks = [{"code": "AAPL", "name": "苹果"}]
        fetcher.save_us_stocks_cache(stocks)

        assert fetcher.us_stock_cache.exists()
        with open(fetcher.us_stock_cache, encoding="utf-8") as f:
            data = json.load(f)
            assert len(data["data"]) == 1

    def test_load_us_stocks_cache(self, fetcher):
        """Test load_us_stocks_cache"""
        stocks = [{"code": "AAPL", "name": "苹果"}]
        fetcher.save_us_stocks_cache(stocks)

        result = fetcher.load_us_stocks_cache()
        assert len(result) == 1

    def test_load_us_stocks_cache_empty(self, fetcher):
        """Test load_us_stocks_cache with no file"""
        result = fetcher.load_us_stocks_cache()
        assert result == []


class TestFetchFuturesQuote:
    """Tests for fetch_futures_quote method"""

    @pytest.fixture
    def fetcher(self):
        """创建测试实例"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            with patch("asset_lens.data.international_stock_fetcher.config") as mock_config:
                mock_config.cache_path = temp_path
                fetcher = InternationalStockFetcher()
                yield fetcher

    def test_fetch_futures_quote_success(self, fetcher):
        """Test fetch_futures_quote success"""
        mock_df = pd.DataFrame(
            {
                "symbol": ["AU0"],
                "name": ["黄金"],
                "trade": [450.0],
                "changepercent": [1.5],
                "change": [6.7],
                "volume": [100000],
                "open": [445.0],
                "high": [452.0],
                "low": [443.0],
            }
        )

        mock_ak = MagicMock()
        mock_ak.futures_main_sina.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.fetch_futures_quote("AU0")

            assert result is not None
            assert result["code"] == "AU0"
            assert result["name"] == "黄金"

    def test_fetch_futures_quote_not_found(self, fetcher):
        """Test fetch_futures_quote not found"""
        mock_df = pd.DataFrame(
            {
                "symbol": ["AU0"],
                "name": ["黄金"],
            }
        )

        mock_ak = MagicMock()
        mock_ak.futures_main_sina.return_value = mock_df

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.fetch_futures_quote("NOTEXIST")
            assert result is None

    def test_fetch_futures_quote_exception(self, fetcher):
        """Test fetch_futures_quote with exception"""
        mock_ak = MagicMock()
        mock_ak.futures_main_sina.side_effect = Exception("API error")

        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = fetcher.fetch_futures_quote("AU0")
            assert result is None
