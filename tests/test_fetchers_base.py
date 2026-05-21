"""
Tests for Data Fetchers Base Module
"""

from datetime import datetime

from asset_lens.data.fetchers.base import BaseFetcher, FetchResult
from asset_lens.data.providers.cache import UnifiedCache


class TestFetchResult:
    """FetchResult 测试"""

    def test_fetch_result_creation(self):
        """测试 FetchResult 创建"""
        result = FetchResult(
            success=True,
            data={"price": 100.0},
            source="test",
        )

        assert result.success is True
        assert result.data == {"price": 100.0}
        assert result.source == "test"
        assert result.timestamp is not None
        assert result.error is None

    def test_fetch_result_with_error(self):
        """测试带错误的 FetchResult"""
        result = FetchResult(
            success=False,
            error="Connection timeout",
            source="test",
        )

        assert result.success is False
        assert result.error == "Connection timeout"
        assert result.data is None

    def test_fetch_result_timestamp_auto_set(self):
        """测试时间戳自动设置"""
        before = datetime.now()
        result = FetchResult(success=True)
        after = datetime.now()

        assert before <= result.timestamp <= after


class ConcreteFetcher(BaseFetcher):
    """具体 Fetcher 实现用于测试"""

    def fetch(self, symbol: str, **kwargs):
        return FetchResult(
            success=True,
            data={"symbol": symbol, "price": 100.0},
            source="test",
        )

    def fetch_batch(self, symbols, **kwargs):
        results = {}
        for symbol in symbols:
            results[symbol] = self.fetch(symbol, **kwargs)
        return results


class TestBaseFetcher:
    """BaseFetcher 测试"""

    def test_fetcher_initialization(self):
        """测试 Fetcher 初始化"""
        fetcher = ConcreteFetcher(timeout=30, max_retries=5)

        assert fetcher.timeout == 30
        assert fetcher.max_retries == 5
        assert isinstance(fetcher._cache, UnifiedCache)

    def test_fetch_method(self):
        """测试 fetch 方法"""
        fetcher = ConcreteFetcher()
        result = fetcher.fetch("AAPL")

        assert result.success is True
        assert result.data["symbol"] == "AAPL"
        assert result.data["price"] == 100.0

    def test_fetch_batch_method(self):
        """测试批量获取方法"""
        fetcher = ConcreteFetcher()
        results = fetcher.fetch_batch(["AAPL", "GOOGL"])

        assert len(results) == 2
        assert "AAPL" in results
        assert "GOOGL" in results
        assert results["AAPL"].success is True

    def test_cache_operations(self):
        """测试缓存操作"""
        fetcher = ConcreteFetcher()

        # 设置缓存
        fetcher.set_cache("test_key", {"price": 100.0})

        # 获取缓存
        cached = fetcher.get_cache("test_key")
        assert cached is not None
        assert cached["data"]["price"] == 100.0

        # 清除缓存
        fetcher.clear_cache()
        assert fetcher.get_cache("test_key") is None

    def test_validate_symbol(self):
        """测试代码验证"""
        fetcher = ConcreteFetcher()

        assert fetcher._validate_symbol("AAPL") is True
        assert fetcher._validate_symbol("") is False
        assert fetcher._validate_symbol(None) is False

    def test_handle_error(self):
        """测试错误处理"""
        fetcher = ConcreteFetcher()
        error = Exception("Test error")
        result = fetcher._handle_error(error, "fetching data")

        assert result.success is False
        assert "Test error" in result.error
        assert result.source == "ConcreteFetcher"

    def test_get_source_name(self):
        """测试获取数据源名称"""
        fetcher = ConcreteFetcher()
        assert fetcher.get_source_name() == "concrete"
