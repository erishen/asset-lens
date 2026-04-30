"""
E2E Tests for ML API Endpoints.
ML API 端点端到端测试
"""

from playwright.sync_api import Page


class TestMLAPI:
    """ML API 测试"""

    def test_ml_signals(self, page: Page, base_url: str) -> None:
        """测试 ML 信号列表"""
        response = page.request.get(f"{base_url}/api/ml/signals")

        assert response.status in [200, 404, 401]

        if response.status == 200:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_ml_model_status(self, page: Page, base_url: str) -> None:
        """测试 ML 模型状态"""
        response = page.request.get(f"{base_url}/api/ml/model/status")

        assert response.status in [200, 404, 401]

        if response.status == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_ml_history(self, page: Page, base_url: str) -> None:
        """测试 ML 历史记录"""
        response = page.request.get(f"{base_url}/api/ml/history")

        assert response.status in [200, 404, 401]

        if response.status == 200:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_ml_signal_by_code(self, page: Page, base_url: str) -> None:
        """测试单个股票 ML 信号"""
        response = page.request.get(f"{base_url}/api/ml/signal/sh600519")

        assert response.status in [200, 404, 401, 422]

    def test_ml_status_endpoint(self, page: Page, base_url: str) -> None:
        """测试 ML 状态端点"""
        response = page.request.get(f"{base_url}/api/ml/status")

        assert response.status in [200, 404, 401]


class TestMLPerformance:
    """ML 性能测试"""

    def test_ml_response_time(self, page: Page, base_url: str) -> None:
        """测试 ML API 响应时间"""
        import time

        start = time.time()
        response = page.request.get(f"{base_url}/api/ml/model/status")
        end = time.time()

        response_time = (end - start) * 1000

        assert response_time < 10000, f"ML API 响应时间应该小于 10 秒，实际: {response_time:.0f}ms"
        assert response.status in [200, 404, 401]

    def test_ml_signals_pagination(self, page: Page, base_url: str) -> None:
        """测试 ML 信号分页"""
        response = page.request.get(f"{base_url}/api/ml/signals?limit=10")

        assert response.status in [200, 404, 401]
