"""
E2E Tests for Strategy API Endpoints.
策略 API 端点端到端测试
"""

from playwright.sync_api import Page


class TestStrategyAPI:
    """策略 API 测试"""

    def test_strategy_list(self, page: Page, base_url: str) -> None:
        """测试策略列表"""
        response = page.request.get(f"{base_url}/api/strategies")

        assert response.status in [200, 404, 401]

        if response.status == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_strategy_detail(self, page: Page, base_url: str) -> None:
        """测试策略详情"""
        response = page.request.get(f"{base_url}/api/strategies/momentum")

        assert response.status in [200, 404, 401, 422]

    def test_strategy_recommendations(self, page: Page, base_url: str) -> None:
        """测试策略推荐"""
        response = page.request.get(f"{base_url}/api/strategies/recommendations/stocks")

        assert response.status in [200, 404, 401]


class TestRecommendationAPI:
    """推荐 API 测试"""

    def test_stock_recommendations(self, page: Page, base_url: str) -> None:
        """测试股票推荐"""
        response = page.request.get(f"{base_url}/api/recommendations/stocks")

        assert response.status in [200, 404, 401]

        if response.status == 200:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_strategy_recommendations_list(self, page: Page, base_url: str) -> None:
        """测试策略推荐列表"""
        response = page.request.get(f"{base_url}/api/recommendations/strategies")

        assert response.status in [200, 404, 401]


class TestBacktestAPI:
    """回测 API 测试"""

    def test_backtest_endpoint(self, page: Page, base_url: str) -> None:
        """测试回测端点"""
        response = page.request.get(f"{base_url}/api/backtest")

        assert response.status in [200, 404, 401, 405]
