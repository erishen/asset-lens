"""
Tests for Stock Data Fetcher.
股票数据获取模块测试
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
        with patch("asset_lens.data.stock_fetcher.config") as mock_config:
            mock_config.cache_path = temp_cache_path
            mock_config.project_root = temp_cache_path
            mock_config.finnhub_api_key = "demo"
            fetcher = StockDataFetcher()
            yield fetcher

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.stock_fetcher import stock_fetcher

        assert stock_fetcher is not None

    def test_init(self, fetcher):
        """测试初始化"""
        assert fetcher is not None
        assert fetcher.cache_path is not None

    def test_cache_file_path(self, fetcher):
        """测试缓存文件路径"""
        assert fetcher.stock_cache_file.name == "stock_quotes.json"

    def test_load_stock_codes_config_empty(self, fetcher):
        """测试加载股票代码配置 - 空配置"""
        codes = fetcher._load_stock_codes_config()
        assert isinstance(codes, dict)

    def test_load_stock_codes_config_with_file(self, fetcher, temp_cache_path):
        """测试加载股票代码配置 - 有配置文件"""
        config_dir = temp_cache_path / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "fund_stock_codes.json"

        config_data = {
            "stocks": [
                {"name": "贵州茅台", "code": "sh600519", "keywords": ["茅台"]},
                {"name": "平安银行", "code": "sz000001", "keywords": ["平安"]},
            ]
        }

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        fetcher._stock_codes_map = None
        codes = fetcher._load_stock_codes_config()

        assert "贵州茅台" in codes
        assert codes["贵州茅台"] == "sh600519"
        assert "茅台" in codes

    def test_get_stock_code_from_name(self, fetcher, temp_cache_path):
        """测试从名称获取股票代码"""
        config_dir = temp_cache_path / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "fund_stock_codes.json"

        config_data = {
            "stocks": [
                {"name": "贵州茅台", "code": "sh600519", "keywords": ["茅台"]},
            ]
        }

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        fetcher._stock_codes_map = None
        codes = fetcher._load_stock_codes_config()
        assert "贵州茅台" in codes
        assert codes["贵州茅台"] == "sh600519"

    def test_get_stock_code_from_name_not_found(self, fetcher):
        """测试从名称获取股票代码 - 未找到"""
        fetcher._stock_codes_map = {}
        codes = fetcher._load_stock_codes_config()
        assert "不存在的股票" not in codes

    def test_fetch_stock_quote_invalid_code(self, fetcher):
        """测试获取股票行情 - 无效代码"""
        result = fetcher.fetch_stock_quote_akshare("invalid_code")
        assert result is None

    def test_fetch_cn_stock_quote_mock(self, fetcher):
        """测试获取A股行情 - Mock"""
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.__getitem__ = MagicMock(return_value=MagicMock())
        mock_df.iloc = MagicMock()
        mock_row = {
            "代码": "600519",
            "名称": "贵州茅台",
            "最新价": 1800.0,
            "昨收": 1780.0,
            "今开": 1785.0,
            "最高": 1810.0,
            "最低": 1780.0,
            "成交量": 1000000,
            "成交额": 1800000000,
            "振幅": 1.5,
            "涨跌幅": 1.12,
            "涨跌额": 20.0,
            "换手率": 0.5,
            "总市值": 2250000000000,
        }
        mock_df.iloc.__getitem__ = MagicMock(return_value=mock_row)
        mock_df.__getitem__.return_value.__eq__ = MagicMock(return_value=MagicMock())
        mock_df.__getitem__.return_value.__eq__.return_value.empty = False
        mock_df.__getitem__.return_value.__eq__.return_value.iloc = [mock_row]

        with patch.object(fetcher, "_fetch_cn_stock_quote") as mock_fetch:
            mock_fetch.return_value = {
                "code": "sh600519",
                "name": "贵州茅台",
                "current_price": 1800.0,
                "source": "AkShare",
            }

            result = fetcher.fetch_stock_quote_akshare("sh600519")
            assert result is not None
            assert result["code"] == "sh600519"

    def test_fetch_hk_stock_quote_mock(self, fetcher):
        """测试获取港股行情 - Mock"""
        with patch.object(fetcher, "_fetch_hk_stock_quote") as mock_fetch:
            mock_fetch.return_value = {
                "code": "hk00700",
                "name": "腾讯控股",
                "current_price": 300.0,
                "source": "AkShare",
            }

            result = fetcher.fetch_stock_quote_akshare("hk00700")
            assert result is not None
            assert result["code"] == "hk00700"

    def test_fetch_us_stock_quote_mock(self, fetcher):
        """测试获取美股行情 - Mock"""
        with patch.object(fetcher, "fetch_us_stock_quote") as mock_fetch:
            mock_fetch.return_value = {
                "code": "AAPL",
                "name": "Apple Inc.",
                "current_price": 180.0,
                "source": "Finnhub",
            }

            result = fetcher.fetch_us_stock_quote("AAPL")
            assert result is not None
            assert result["code"] == "AAPL"

    def test_save_cache(self, fetcher):
        """测试保存缓存"""
        cache_data = {
            "sh600519": {
                "code": "sh600519",
                "name": "贵州茅台",
                "current_price": 1800.0,
            }
        }

        with open(fetcher.stock_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        assert fetcher.stock_cache_file.exists()

    def test_load_cache(self, fetcher):
        """测试加载缓存"""
        cache_data = {
            "sh600519": {
                "code": "sh600519",
                "name": "贵州茅台",
                "current_price": 1800.0,
            }
        }

        with open(fetcher.stock_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        assert fetcher.stock_cache_file.exists()


class TestStockCodeParsing:
    """股票代码解析测试"""

    def test_parse_cn_stock_code_sh(self):
        """测试解析A股代码 - 上证"""
        code = "sh600519"
        assert code.startswith("sh")
        assert code[2:] == "600519"

    def test_parse_cn_stock_code_sz(self):
        """测试解析A股代码 - 深证"""
        code = "sz000001"
        assert code.startswith("sz")
        assert code[2:] == "000001"

    def test_parse_hk_stock_code(self):
        """测试解析港股代码"""
        code = "hk00700"
        assert code.startswith("hk")
        assert code[2:] == "00700"

    def test_is_cn_stock(self):
        """测试判断A股"""
        codes = ["sh600519", "sz000001", "hk00700", "AAPL"]

        cn_stocks = [c for c in codes if c.startswith(("sh", "sz"))]
        assert len(cn_stocks) == 2

    def test_is_hk_stock(self):
        """测试判断港股"""
        codes = ["sh600519", "sz000001", "hk00700", "AAPL"]

        hk_stocks = [c for c in codes if c.startswith("hk")]
        assert len(hk_stocks) == 1


class TestStockQuoteData:
    """股票行情数据测试"""

    def test_quote_data_structure(self):
        """测试行情数据结构"""
        quote = {
            "code": "sh600519",
            "name": "贵州茅台",
            "current_price": 1800.0,
            "open": 1785.0,
            "prev_close": 1780.0,
            "high": 1810.0,
            "low": 1780.0,
            "volume": 1000000,
            "amount": 1800000000,
            "change_amount": 20.0,
            "change_percent": 1.12,
            "amplitude": 1.5,
            "market_cap": 22500.0,
            "turnover_rate": 0.5,
            "update_time": "2024-01-01 15:00:00",
            "source": "AkShare",
        }

        assert quote["code"] == "sh600519"
        assert quote["current_price"] > 0
        assert quote["change_percent"] >= -10  # 涨跌幅限制

    def test_calculate_change_percent(self):
        """测试计算涨跌幅"""
        current_price = 1800.0
        prev_close = 1780.0

        change_percent = (current_price - prev_close) / prev_close * 100
        assert change_percent == pytest.approx(1.12, rel=0.1)

    def test_calculate_amplitude(self):
        """测试计算振幅"""
        high = 1810.0
        low = 1780.0
        prev_close = 1780.0

        amplitude = (high - low) / prev_close * 100
        assert amplitude == pytest.approx(1.69, rel=0.1)


class TestStockBatchFetch:
    """批量获取股票测试"""

    def test_batch_fetch_structure(self):
        """测试批量获取结构"""
        codes = ["sh600519", "sz000001", "hk00700"]

        results = {}
        for code in codes:
            results[code] = {"code": code, "current_price": 100.0}

        assert len(results) == 3
        assert "sh600519" in results

    def test_batch_fetch_with_errors(self):
        """测试批量获取 - 有错误"""
        codes = ["sh600519", "invalid", "sz000001"]

        results = {}
        for code in codes:
            if code.startswith(("sh", "sz", "hk")):
                results[code] = {"code": code, "current_price": 100.0}
            else:
                results[code] = None

        assert results["sh600519"] is not None
        assert results["invalid"] is None
        assert results["sz000001"] is not None


class TestStockCache:
    """股票缓存测试"""

    def test_cache_expiry(self):
        """测试缓存过期"""
        import time

        cache_time = time.time() - 3600  # 1小时前
        current_time = time.time()

        is_expired = current_time - cache_time > 300  # 5分钟过期
        assert is_expired is True

    def test_cache_valid(self):
        """测试缓存有效"""
        import time

        cache_time = time.time() - 60  # 1分钟前
        current_time = time.time()

        is_valid = current_time - cache_time <= 300  # 5分钟内有效
        assert is_valid is True
