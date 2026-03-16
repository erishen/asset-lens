"""
Tests for Multi-Source Data Fetcher
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from asset_lens.data.multi_source_fetcher import (
    MultiSourceDataFetcher,
    DataSourceStatus,
    DataSourceConfig,
)


@pytest.fixture
def fetcher():
    """创建多数据源获取器实例 - Mock 网络请求"""
    with patch.object(MultiSourceDataFetcher, '_initialize_sources'):
        with patch.object(MultiSourceDataFetcher, '_check_source_health', return_value=True):
            return MultiSourceDataFetcher()


class TestDataSourceConfig:
    """测试数据源配置"""

    def test_config_creation(self):
        """测试创建配置"""
        config = DataSourceConfig(
            name="akshare",
            priority=1,
            enabled=True,
            timeout=30,
            max_retries=3,
        )

        assert config.name == "akshare"
        assert config.priority == 1
        assert config.enabled is True
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.status == DataSourceStatus.HEALTHY

    def test_config_defaults(self):
        """测试配置默认值"""
        config = DataSourceConfig(name="test")

        assert config.priority == 0
        assert config.enabled is True
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.error_count == 0
        assert config.success_count == 0


class TestMultiSourceDataFetcher:
    """测试多数据源获取器"""

    def test_init(self, fetcher):
        """测试初始化"""
        assert fetcher.cache_path is not None
        assert fetcher.config_file is not None
        assert len(fetcher.sources) > 0

    def test_get_available_sources(self, fetcher):
        """测试获取可用数据源列表"""
        sources = fetcher.get_available_sources()

        assert isinstance(sources, list)
        assert len(sources) > 0
        assert "akshare" in sources

    def test_sources_priority(self, fetcher):
        """测试数据源优先级排序"""
        sources = fetcher.get_available_sources()

        priorities = [fetcher.sources[s].priority for s in sources]
        assert priorities == sorted(priorities)

    def test_fetch_quote_akshare_success(self, fetcher):
        """测试使用 AkShare 获取行情 - 成功"""
        with patch.object(fetcher, '_fetch_quote_akshare') as mock_method:
            mock_method.return_value = {
                "code": "sh600519",
                "name": "贵州茅台",
                "current_price": 1800.0,
                "data_source": "akshare",
            }

            quote = fetcher._fetch_quote_akshare("sh600519")

            assert quote is not None
            assert quote["code"] == "sh600519"
            assert quote["name"] == "贵州茅台"
            assert quote["current_price"] == 1800.0
            assert quote["data_source"] == "akshare"

    def test_fetch_quote_akshare_not_found(self, fetcher):
        """测试使用 AkShare 获取行情 - 未找到"""
        with patch.object(fetcher, '_fetch_quote_akshare') as mock_method:
            mock_method.return_value = None

            quote = fetcher._fetch_quote_akshare("sh600519")

            assert quote is None

    def test_fetch_quote_akshare_error(self, fetcher):
        """测试使用 AkShare 获取行情 - 错误"""
        with patch.object(fetcher, '_fetch_quote_akshare') as mock_method:
            mock_method.return_value = None

            quote = fetcher._fetch_quote_akshare("sh600519")

            assert quote is None

    def test_fetch_quote_tushare_no_token(self, fetcher):
        """测试使用 Tushare 获取行情 - 无 Token"""
        with patch.object(fetcher, '_fetch_quote_tushare') as mock_method:
            mock_method.return_value = None

            quote = fetcher._fetch_quote_tushare("sh600519")

            assert quote is None

    def test_fetch_quote_baostock_error(self, fetcher):
        """测试使用 Baostock 获取行情 - 登录失败"""
        with patch.object(fetcher, '_fetch_quote_baostock') as mock_method:
            mock_method.return_value = None

            quote = fetcher._fetch_quote_baostock("sh600519")

            assert quote is None

    def test_fetch_with_fallback_success(self, fetcher):
        """测试故障切换 - 成功"""
        def mock_fetch(source_name):
            return {"data": "test"}

        result = fetcher.fetch_with_fallback(mock_fetch, ["akshare"])

        assert result is not None
        assert result["data"] == "test"

    def test_fetch_with_fallback_all_failed(self, fetcher):
        """测试故障切换 - 全部失败"""
        def mock_fetch(source_name):
            raise Exception("All sources failed")

        with pytest.raises(Exception):
            fetcher.fetch_with_fallback(mock_fetch, ["akshare"])

    def test_enable_source(self, fetcher):
        """测试启用数据源"""
        fetcher.sources["test"] = DataSourceConfig(name="test", enabled=False)

        result = fetcher.enable_source("test")

        assert result is True
        assert fetcher.sources["test"].enabled is True

    def test_enable_source_nonexistent(self, fetcher):
        """测试启用不存在的数据源"""
        result = fetcher.enable_source("nonexistent")

        assert result is False

    def test_disable_source(self, fetcher):
        """测试禁用数据源"""
        fetcher.sources["test"] = DataSourceConfig(name="test", enabled=True)

        result = fetcher.disable_source("test")

        assert result is True
        assert fetcher.sources["test"].enabled is False

    def test_set_source_priority(self, fetcher):
        """测试设置数据源优先级"""
        fetcher.sources["test"] = DataSourceConfig(name="test", priority=1)

        result = fetcher.set_source_priority("test", 5)

        assert result is True
        assert fetcher.sources["test"].priority == 5

    def test_reset_source_status(self, fetcher):
        """测试重置数据源状态"""
        fetcher.sources["test"] = DataSourceConfig(
            name="test",
            status=DataSourceStatus.UNAVAILABLE,
            error_count=10,
            success_count=5,
        )

        result = fetcher.reset_source_status("test")

        assert result is True
        assert fetcher.sources["test"].status == DataSourceStatus.HEALTHY
        assert fetcher.sources["test"].error_count == 0
        assert fetcher.sources["test"].success_count == 0

    def test_get_source_status(self, fetcher):
        """测试获取数据源状态"""
        status = fetcher.get_source_status()

        assert "update_time" in status
        assert "sources" in status
        assert "available_sources" in status
        assert isinstance(status["sources"], dict)
        assert isinstance(status["available_sources"], list)

    def test_fetch_stock_quote(self, fetcher):
        """测试获取股票行情"""
        with patch.object(fetcher, 'fetch_stock_quote') as mock_method:
            mock_method.return_value = {
                "code": "sh600519",
                "name": "贵州茅台",
                "current_price": 1800.0,
                "data_source": "akshare",
            }

            quote = fetcher.fetch_stock_quote("sh600519")

            assert quote is not None
            assert quote["code"] == "sh600519"
