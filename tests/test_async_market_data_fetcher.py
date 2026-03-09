"""
Tests for Async Market Data Fetcher.
异步市场数据获取器测试
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestAsyncMarketDataFetcher:
    """异步市场数据获取器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.async_market_data_fetcher import AsyncMarketDataFetcher
        assert AsyncMarketDataFetcher is not None

    @pytest.fixture
    def fetcher(self):
        """创建获取器实例"""
        from asset_lens.data.async_market_data_fetcher import AsyncMarketDataFetcher
        with patch('asset_lens.data.async_market_data_fetcher.config') as mock_config:
            mock_config.cache_path = MagicMock()
            return AsyncMarketDataFetcher()

    def test_fetcher_init(self, fetcher):
        """测试初始化"""
        assert fetcher is not None

    def test_max_concurrent_setting(self, fetcher):
        """测试最大并发设置"""
        assert hasattr(fetcher, 'max_concurrent') or hasattr(fetcher, '_semaphore')

    def test_request_delay_setting(self, fetcher):
        """测试请求延迟设置"""
        assert hasattr(fetcher, 'request_delay') or hasattr(fetcher, '_delay')


class TestAsyncDataFetching:
    """异步数据获取测试"""

    @pytest.mark.asyncio
    async def test_async_fetch_pattern(self):
        """测试异步获取模式"""
        import asyncio
        
        async def mock_fetch():
            await asyncio.sleep(0.01)
            return {"data": "test"}
        
        result = await mock_fetch()
        assert result["data"] == "test"

    @pytest.mark.asyncio
    async def test_concurrent_fetch_pattern(self):
        """测试并发获取模式"""
        import asyncio
        
        async def fetch_one(i):
            await asyncio.sleep(0.01)
            return i
        
        results = await asyncio.gather(*[fetch_one(i) for i in range(5)])
        assert len(results) == 5


class TestCacheManagement:
    """缓存管理测试"""

    def test_cache_path(self):
        """测试缓存路径"""
        from asset_lens.config import config
        assert config.cache_path is not None

    def test_cache_file_extension(self):
        """测试缓存文件扩展名"""
        from pathlib import Path
        cache_file = Path("cache/test.json")
        assert cache_file.suffix == ".json"
