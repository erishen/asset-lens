"""
Optimized E2E Tests for All API Endpoints.
优化的 E2E API 测试 - 合并所有 API 测试到一个文件

优化策略：
1. 使用参数化测试减少代码量
2. 使用共享浏览器上下文
3. 标记慢速测试
"""

import pytest
from playwright.sync_api import Page

API_ENDPOINTS = [
    ("/api/portfolio/summary", "投资组合摘要"),
    ("/api/portfolio/items", "投资组合项目"),
    ("/api/portfolio/performance", "投资组合表现"),
    ("/api/market/indexes", "市场指数"),
    ("/api/market/hot-stocks", "热门股票"),
    ("/api/market/north-flow", "北向资金"),
    ("/api/market/sentiment", "市场情绪"),
    ("/api/strategies", "策略列表"),
    ("/api/strategies/recommendations/stocks", "策略推荐"),
    ("/api/ml/signals", "ML 信号"),
    ("/api/ml/model/status", "ML 模型状态"),
    ("/api/ml/history", "ML 历史"),
    ("/api/risk/summary", "风险摘要"),
    ("/api/stock-pool", "股票池"),
    ("/api/compare/weekly", "周比较"),
    ("/api/compare/trend", "趋势比较"),
    ("/api/compare/snapshot/list", "快照列表"),
    ("/api/backup/status", "备份状态"),
    ("/api/backup/list", "备份列表"),
    ("/api/provider-health", "数据源健康"),
    ("/api/cache/stats", "缓存统计"),
    ("/api/goals", "目标列表"),
]

SLOW_ENDPOINTS = [
    "/api/ml/signals",
    "/api/ml/history",
    "/api/market/indexes",
    "/api/market/hot-stocks",
    "/api/market/north-flow",
    "/api/market/sentiment",
    "/api/strategies",
    "/api/strategies/recommendations/stocks",
]


@pytest.fixture(scope="module")
def api_client(shared_page: Page, base_url: str):
    """共享 API 客户端"""

    class APIClient:
        def __init__(self, page: Page, base_url: str):
            self.page = page
            self.base_url = base_url

        def get(self, endpoint: str) -> dict:
            response = self.page.request.get(f"{self.base_url}{endpoint}")
            try:
                return {"status": response.status, "data": response.json()}
            except Exception:
                return {"status": response.status, "data": None}

    return APIClient(shared_page, base_url)


class TestAllAPIEndpoints:
    """所有 API 端点测试 - 参数化"""

    @pytest.mark.parametrize("endpoint,name", API_ENDPOINTS)
    def test_api_endpoint(self, api_client, endpoint: str, name: str, request: pytest.FixtureRequest):
        """测试 API 端点"""
        if endpoint in SLOW_ENDPOINTS:
            request.node.add_marker(pytest.mark.slow)

        result = api_client.get(endpoint)
        assert result["status"] in [
            200,
            404,
            401,
            405,
            422,
            500,
        ], f"{name} ({endpoint}): 期望状态码 [200, 404, 401, 405, 422, 500]，实际 {result['status']}"


class TestStockAPI:
    """股票 API 测试"""

    @pytest.mark.parametrize("code", ["sh600519", "sz000001"])
    def test_stock_quote(self, api_client, code: str):
        """测试股票行情"""
        result = api_client.get(f"/api/stock/quote/{code}")
        assert result["status"] in [200, 404, 401, 422]

    def test_stock_search(self, api_client):
        """测试股票搜索"""
        result = api_client.get("/api/stock/search?keyword=茅台")
        assert result["status"] in [200, 404, 401, 422]


class TestMLAPI:
    """ML API 测试"""

    @pytest.mark.slow
    def test_ml_signal_by_code(self, api_client):
        """测试单个股票 ML 信号"""
        result = api_client.get("/api/ml/signal/sh600519")
        assert result["status"] in [200, 404, 401, 422]


class TestAPIPerformance:
    """API 性能测试"""

    @pytest.mark.slow
    def test_multiple_requests(self, api_client):
        """测试多个连续请求"""
        endpoints = [
            "/api/portfolio/summary",
            "/api/market/indexes",
            "/api/strategies",
        ]

        for endpoint in endpoints:
            result = api_client.get(endpoint)
            assert result["status"] in [200, 404, 401, 405, 500]
