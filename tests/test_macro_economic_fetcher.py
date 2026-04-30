"""
Tests for macro_economic_fetcher module.
宏观经济数据获取模块测试
"""

from unittest.mock import MagicMock, patch

from asset_lens.data.macro_economic_fetcher import MacroEconomicFetcher, get_macro_fetcher


class TestMacroEconomicFetcher:
    """MacroEconomicFetcher 测试"""

    def test_init(self):
        """测试初始化"""
        fetcher = MacroEconomicFetcher()
        assert fetcher._fred_api_key is None
        assert fetcher._cache == {}

    def test_init_with_api_key(self):
        """测试带 API Key 初始化"""
        fetcher = MacroEconomicFetcher(fred_api_key="test_key")
        assert fetcher._fred_api_key == "test_key"

    def test_indicators_defined(self):
        """测试指标定义"""
        assert "us_gdp" in MacroEconomicFetcher.INDICATORS
        assert "us_cpi" in MacroEconomicFetcher.INDICATORS

    def test_cache_valid(self):
        """测试缓存有效性"""
        fetcher = MacroEconomicFetcher()
        fetcher._cache_time["test"] = 0
        assert not fetcher._is_cache_valid("test")

    def test_clear_cache(self):
        """测试清除缓存"""
        fetcher = MacroEconomicFetcher()
        fetcher._cache["test"] = {"data": "value"}
        fetcher._cache_time["test"] = 100
        fetcher._cache.clear()
        assert "test" not in fetcher._cache


class TestMacroEconomicFetcherWithMock:
    """MacroEconomicFetcher Mock 测试"""

    @patch("asset_lens.data.macro_economic_fetcher.MacroEconomicFetcher.requests")
    def test_fetch_world_bank_indicator_success(self, mock_requests):
        """测试获取世界银行数据成功"""
        fetcher = MacroEconomicFetcher()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"page": 1},
            [
                {
                    "country": {"value": "China"},
                    "countryiso3code": "CHN",
                    "date": "2023",
                    "value": 17963171.0,
                }
            ],
        ]
        mock_requests.get.return_value = mock_response

        result = fetcher.fetch_world_bank_indicator("NY.GDP.MKTP.CD", country="CHN")

        assert result is not None
        assert result["indicator_id"] == "NY.GDP.MKTP.CD"
        assert len(result["observations"]) == 1

    @patch("asset_lens.data.macro_economic_fetcher.MacroEconomicFetcher.requests")
    def test_fetch_world_bank_indicator_error(self, mock_requests):
        """测试获取世界银行数据失败"""
        fetcher = MacroEconomicFetcher()

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_requests.get.return_value = mock_response

        result = fetcher.fetch_world_bank_indicator("NY.GDP.MKTP.CD")
        assert result is None

    def test_get_indicator_unknown(self):
        """测试获取未知指标"""
        fetcher = MacroEconomicFetcher()
        result = fetcher.get_indicator("unknown_indicator")
        assert result is None


class TestGetMacroFetcher:
    """get_macro_fetcher 测试"""

    def test_singleton(self):
        """测试单例模式"""
        import asset_lens.data.macro_economic_fetcher as module

        module._macro_fetcher = None

        fetcher1 = get_macro_fetcher()
        fetcher2 = get_macro_fetcher()

        assert fetcher1 is fetcher2
