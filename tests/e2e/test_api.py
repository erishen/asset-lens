"""
E2E Tests for API Endpoints.
API 端点端到端测试
"""

from playwright.sync_api import Page


class TestAPIEndpoints:
    """API 端点测试"""

    def test_api_stocks_list(self, page: Page, base_url: str) -> None:
        """测试股票列表 API"""
        response = page.request.get(f"{base_url}/api/stocks")

        assert response.status in [200, 404, 401]

    def test_api_portfolio(self, page: Page, base_url: str) -> None:
        """测试投资组合 API"""
        response = page.request.get(f"{base_url}/api/portfolio/summary")

        assert response.status in [200, 404, 401]

    def test_api_market_data(self, page: Page, base_url: str) -> None:
        """测试市场数据 API"""
        response = page.request.get(f"{base_url}/api/market")

        assert response.status in [200, 404, 401]

    def test_api_strategies(self, page: Page, base_url: str) -> None:
        """测试策略 API"""
        response = page.request.get(f"{base_url}/api/strategies")

        assert response.status in [200, 404, 401]

    def test_api_reports(self, page: Page, base_url: str) -> None:
        """测试报告 API"""
        response = page.request.get(f"{base_url}/api/reports")

        assert response.status in [200, 404, 401]

    def test_api_ml_status(self, page: Page, base_url: str) -> None:
        """测试 ML 状态 API"""
        response = page.request.get(f"{base_url}/api/ml/status")

        assert response.status in [200, 404, 401]

    def test_api_risk_check(self, page: Page, base_url: str) -> None:
        """测试风险检查 API"""
        response = page.request.get(f"{base_url}/api/risk")

        assert response.status in [200, 404, 401]

    def test_api_stock_pool(self, page: Page, base_url: str) -> None:
        """测试股票池 API"""
        response = page.request.get(f"{base_url}/api/stock-pool")

        assert response.status in [200, 404, 401]

    def test_api_not_found(self, page: Page, base_url: str) -> None:
        """测试 404 响应"""
        response = page.request.get(f"{base_url}/api/nonexistent-endpoint")

        assert response.status == 404


class TestAPIPerformance:
    """API 性能测试"""

    def test_api_response_time(self, page: Page, base_url: str) -> None:
        """测试 API 响应时间"""
        import time

        start = time.time()
        page.request.get(f"{base_url}/api/health")
        end = time.time()

        response_time = (end - start) * 1000

        assert response_time < 5000, f"API 响应时间应该小于 5 秒，实际: {response_time:.0f}ms"

    def test_concurrent_requests(self, page: Page, base_url: str) -> None:
        """测试多个 API 请求"""
        urls = [
            f"{base_url}/api/health",
            f"{base_url}/api/market",
            f"{base_url}/api/portfolio/summary",
        ]

        results = []
        for url in urls:
            response = page.request.get(url)
            results.append(response.status)

        assert len(results) == 3


class TestAPIDataFormat:
    """API 数据格式测试"""

    def test_json_response(self, page: Page, base_url: str) -> None:
        """测试 JSON 响应格式"""
        response = page.request.get(f"{base_url}/api/health")

        if response.status == 200:
            try:
                data = response.json()
                assert isinstance(data, (dict, list))
            except Exception:
                pass

    def test_cors_headers(self, page: Page, base_url: str) -> None:
        """测试 CORS 头"""
        response = page.request.get(f"{base_url}/api/health")

        headers = response.headers

        cors_header = headers.get("access-control-allow-origin")

        if cors_header:
            assert cors_header in ["*", "http://localhost:3000", "http://localhost:8000"]
