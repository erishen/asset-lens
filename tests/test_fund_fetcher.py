"""
Tests for fund_fetcher.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.data.fund_fetcher import FundDataFetcher, timeout_context


class TestTimeoutContext:
    """timeout_context 测试"""

    def test_timeout_context_normal(self):
        """测试正常执行"""
        with timeout_context(5):
            result = 1 + 1
        assert result == 2

    def test_timeout_context_timeout(self):
        """测试超时"""
        import time

        with pytest.raises(TimeoutError), timeout_context(1, "测试超时"):
            time.sleep(2)


class TestFundDataFetcher:
    """FundDataFetcher 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def fetcher(self, temp_cache_path):
        """创建测试实例"""
        with patch("asset_lens.data.fund_fetcher.config") as mock_config:
            mock_config.cache_path = temp_cache_path
            mock_config.project_root = temp_cache_path
            fetcher = FundDataFetcher()
            yield fetcher

    def test_init(self, fetcher, temp_cache_path):
        """测试初始化"""
        assert fetcher.cache_path == temp_cache_path
        assert fetcher._fund_codes_map is None
        assert fetcher._akshare is None

    def test_init_with_cache_path(self, temp_cache_path):
        """测试带缓存路径初始化"""
        fetcher = FundDataFetcher(cache_path=temp_cache_path)
        assert fetcher.cache_path == temp_cache_path

    def test_akshare_lazy_load(self, fetcher):
        """测试 AkShare 延迟加载"""
        mock_ak = MagicMock()
        with patch.dict("sys.modules", {"akshare": mock_ak}):
            ak = fetcher.akshare
            assert ak == mock_ak

    def test_akshare_import_error(self, fetcher):
        """测试 AkShare 未安装"""
        with patch.dict("sys.modules", {"akshare": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module")):
                fetcher._akshare = None
                with pytest.raises(ImportError) as exc_info:
                    _ = fetcher.akshare
                assert "请先安装 AkShare" in str(exc_info.value)

    def test_load_fund_codes_config_success(self, fetcher, temp_cache_path):
        """测试加载基金代码配置成功"""
        config_dir = temp_cache_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "fund_stock_codes.json"

        config_data = {"funds": [{"name": "测试基金", "code": "000001", "keywords": ["测试", "基金"]}]}

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        result = fetcher._load_fund_codes_config()

        assert "测试基金" in result
        assert result["测试基金"] == "000001"
        assert "测试" in result
        assert result["测试"] == "000001"

    def test_load_fund_codes_config_no_file(self, fetcher):
        """测试加载基金代码配置 - 文件不存在"""
        result = fetcher._load_fund_codes_config()
        assert result == {}

    def test_load_fund_codes_config_exception(self, fetcher, temp_cache_path):
        """测试加载基金代码配置 - 异常"""
        config_dir = temp_cache_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "fund_stock_codes.json"

        with open(config_file, "w", encoding="utf-8") as f:
            f.write("invalid json")

        result = fetcher._load_fund_codes_config()
        assert result == {}

    def test_load_fund_codes_config_cached(self, fetcher, temp_cache_path):
        """测试加载基金代码配置 - 缓存"""
        fetcher._fund_codes_map = {"cached": "000002"}

        result = fetcher._load_fund_codes_config()
        assert result == {"cached": "000002"}

    def test_fetch_fund_quote_akshare_empty_df(self, fetcher):
        """测试获取基金净值 - 空数据"""
        mock_ak = MagicMock()
        mock_ak.fund_open_fund_info_em = MagicMock(return_value=None)
        fetcher._akshare = mock_ak

        result = fetcher.fetch_fund_quote_akshare("000001")
        assert result is None

    def test_fetch_fund_quote_akshare_exception(self, fetcher):
        """测试获取基金净值 - 异常"""
        mock_ak = MagicMock()
        mock_ak.fund_open_fund_info_em = MagicMock(side_effect=Exception("Network error"))
        fetcher._akshare = mock_ak

        result = fetcher.fetch_fund_quote_akshare("000001")
        assert result is None

    def test_fetch_fund_quote_eastmoney(self, fetcher):
        """测试获取基金净值 - 兼容接口"""
        fetcher.fetch_fund_quote_akshare = MagicMock(return_value={"code": "000001"})

        result = fetcher.fetch_fund_quote_eastmoney("000001")
        assert result == {"code": "000001"}

    def test_fetch_fund_info_empty_df(self, fetcher):
        """测试获取基金信息 - 空数据"""
        mock_ak = MagicMock()
        mock_ak.fund_open_fund_info_em = MagicMock(return_value=None)
        fetcher._akshare = mock_ak

        result = fetcher.fetch_fund_info("000001")
        assert result is None

    def test_fetch_fund_info_exception(self, fetcher):
        """测试获取基金信息 - 异常"""
        mock_ak = MagicMock()
        mock_ak.fund_open_fund_info_em = MagicMock(side_effect=Exception("Network error"))
        fetcher._akshare = mock_ak

        result = fetcher.fetch_fund_info("000001")
        assert result is None

    def test_fetch_fund_historical_nav_empty_df(self, fetcher):
        """测试获取基金历史净值 - 空数据"""
        mock_ak = MagicMock()
        mock_ak.fund_open_fund_info_em = MagicMock(return_value=None)
        fetcher._akshare = mock_ak

        result = fetcher.fetch_fund_historical_nav("000001")
        assert result is None

    def test_fetch_fund_historical_nav_exception(self, fetcher):
        """测试获取基金历史净值 - 异常"""
        mock_ak = MagicMock()
        mock_ak.fund_open_fund_info_em = MagicMock(side_effect=Exception("Network error"))
        fetcher._akshare = mock_ak

        result = fetcher.fetch_fund_historical_nav("000001")
        assert result is None

    def test_get_cached_funds_no_cache(self, fetcher):
        """测试获取缓存基金 - 无缓存"""
        result = fetcher.get_cached_funds()
        assert result == {}

    def test_get_cached_funds_with_cache(self, fetcher, temp_cache_path):
        """测试获取缓存基金 - 有缓存"""
        cache_data = {"000001": {"code": "000001", "name": "测试基金"}}

        cache_file = temp_cache_path / "fund_quotes.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        result = fetcher.get_cached_funds()
        assert "000001" in result

    def test_search_fund_empty_df(self, fetcher):
        """测试搜索基金 - 空数据"""
        mock_ak = MagicMock()
        mock_ak.fund_open_fund_daily_em = MagicMock(return_value=None)
        fetcher._akshare = mock_ak

        result = fetcher.search_fund("测试")
        assert result == []

    def test_search_fund_exception(self, fetcher):
        """测试搜索基金 - 异常"""
        mock_ak = MagicMock()
        mock_ak.fund_open_fund_daily_em = MagicMock(side_effect=Exception("Network error"))
        fetcher._akshare = mock_ak

        result = fetcher.search_fund("测试")
        assert result == []


class TestAutoMatchFundCodes:
    """auto_match_fund_codes 测试"""

    def test_auto_match_fund_codes_success(self):
        """测试自动匹配基金代码成功"""
        with patch("asset_lens.data.fund_fetcher.fund_fetcher") as mock_fetcher:
            mock_fetcher._load_fund_codes_config = MagicMock(
                return_value={
                    "测试基金": "000001",
                    "股票基金": "000002",
                }
            )

            from asset_lens.data.fund_fetcher import auto_match_fund_codes

            result = auto_match_fund_codes(["测试基金", "股票基金"])

            assert "测试基金" in result
            assert result["测试基金"] == "000001"

    def test_auto_match_fund_codes_skip_keywords(self):
        """测试自动匹配基金代码 - 跳过关键词"""
        with patch("asset_lens.data.fund_fetcher.fund_fetcher") as mock_fetcher:
            mock_fetcher._load_fund_codes_config = MagicMock(return_value={})

            from asset_lens.data.fund_fetcher import auto_match_fund_codes

            result = auto_match_fund_codes(["余额宝", "活期富", "货币基金"])

            assert result["余额宝"] is None
            assert result["活期富"] is None
            assert result["货币基金"] is None

    def test_auto_match_fund_codes_empty_name(self):
        """测试自动匹配基金代码 - 空名称"""
        with patch("asset_lens.data.fund_fetcher.fund_fetcher") as mock_fetcher:
            mock_fetcher._load_fund_codes_config = MagicMock(return_value={})

            from asset_lens.data.fund_fetcher import auto_match_fund_codes

            result = auto_match_fund_codes(["", "   "])

            assert result[""] is None

    def test_auto_match_fund_codes_partial_match(self):
        """测试自动匹配基金代码 - 部分匹配"""
        with patch("asset_lens.data.fund_fetcher.fund_fetcher") as mock_fetcher:
            mock_fetcher._load_fund_codes_config = MagicMock(
                return_value={
                    "易方达": "000001",
                }
            )

            from asset_lens.data.fund_fetcher import auto_match_fund_codes

            result = auto_match_fund_codes(["易方达蓝筹精选"])

            assert "易方达蓝筹精选" in result
            assert result["易方达蓝筹精选"] == "000001"


class TestFetchPortfolioFundQuotes:
    """fetch_portfolio_fund_quotes 测试"""

    def test_fetch_portfolio_fund_quotes(self):
        """测试获取投资组合基金净值"""
        with patch("asset_lens.data.fund_fetcher.fund_fetcher") as mock_fetcher:
            mock_fetcher.fetch_multiple_funds = MagicMock(
                return_value={"000001": {"code": "000001", "current_nav": 1.5}}
            )

            from asset_lens.data.fund_fetcher import fetch_portfolio_fund_quotes

            result = fetch_portfolio_fund_quotes()

            assert isinstance(result, dict)
