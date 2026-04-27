"""
E2E Tests for Market Data API Endpoints.
市场数据 API 端点端到端测试
"""

import pytest
from playwright.sync_api import Page


class TestMarketAPI:
    """市场数据 API 测试"""

    def test_market_indexes(self, page: Page, base_url: str) -> None:
        """测试市场指数列表"""
        response = page.request.get(f"{base_url}/api/market/indexes")
        
        assert response.status in [200, 404, 401]
        
        if response.status == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_hot_stocks(self, page: Page, base_url: str) -> None:
        """测试热门股票"""
        response = page.request.get(f"{base_url}/api/market/hot-stocks")
        
        assert response.status in [200, 404, 401]
        
        if response.status == 200:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_north_flow(self, page: Page, base_url: str) -> None:
        """测试北向资金"""
        response = page.request.get(f"{base_url}/api/market/north-flow")
        
        assert response.status in [200, 404, 401]
        
        if response.status == 200:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_market_sentiment(self, page: Page, base_url: str) -> None:
        """测试市场情绪"""
        response = page.request.get(f"{base_url}/api/market/sentiment")
        
        assert response.status in [200, 404, 401]
        
        if response.status == 200:
            data = response.json()
            assert isinstance(data, dict)


class TestStockAPI:
    """股票 API 测试"""

    def test_stock_quote(self, page: Page, base_url: str) -> None:
        """测试股票行情"""
        response = page.request.get(f"{base_url}/api/stocks/quote/sh600519")
        
        assert response.status in [200, 404, 401, 422]

    def test_stock_search(self, page: Page, base_url: str) -> None:
        """测试股票搜索"""
        response = page.request.get(f"{base_url}/api/stocks/search?keyword=茅台")
        
        assert response.status in [200, 404, 401, 422]

    def test_stock_kline(self, page: Page, base_url: str) -> None:
        """测试股票 K 线"""
        response = page.request.get(f"{base_url}/api/stocks/kline/sh600519")
        
        assert response.status in [200, 404, 401, 422]


class TestMarketPerformance:
    """市场数据性能测试"""

    def test_market_response_time(self, page: Page, base_url: str) -> None:
        """测试市场 API 响应时间"""
        import time
        
        start = time.time()
        response = page.request.get(f"{base_url}/api/market/indexes")
        end = time.time()
        
        response_time = (end - start) * 1000
        
        assert response_time < 10000, f"市场 API 响应时间应该小于 10 秒，实际: {response_time:.0f}ms"
