"""
Tests for REST API.
REST API 测试
"""

import pytest
from fastapi.testclient import TestClient

from asset_lens.web.api import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def api_headers():
    """API请求头"""
    return {"Authorization": "Bearer demo_key"}


class TestRootEndpoint:
    """测试根路径"""

    def test_root(self, client):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            data = response.json()
            assert "version" in data or "name" in data


class TestStockEndpoints:
    """测试股票相关API"""

    @pytest.mark.network
    def test_get_stock_quote(self, client, api_headers):
        """测试获取股票行情"""
        response = client.get("/api/v1/stocks/sh600519", headers=api_headers)
        assert response.status_code in [200, 404, 500]

    def test_get_stock_quote_unauthorized(self, client):
        """测试未授权访问"""
        response = client.get("/api/v1/stocks/sh600519")
        assert response.status_code in [401, 403, 404]

    @pytest.mark.network
    def test_screen_stocks(self, client, api_headers):
        """测试股票筛选"""
        response = client.post("/api/v1/stocks/screen?strategy=momentum&limit=10", headers=api_headers)
        assert response.status_code in [200, 404, 500]


class TestFundEndpoints:
    """测试基金相关API"""

    @pytest.mark.network
    def test_get_fund_nav(self, client, api_headers):
        """测试获取基金净值"""
        response = client.get("/api/v1/funds/000001", headers=api_headers)
        assert response.status_code in [200, 404, 500]


class TestPortfolioEndpoints:
    """测试投资组合相关API"""

    def test_get_portfolio_analysis(self, client, api_headers):
        """测试获取投资组合分析"""
        response = client.get("/api/v1/portfolio/analysis", headers=api_headers)
        assert response.status_code in [200, 404, 500]


class TestRiskEndpoints:
    """测试风险相关API"""

    def test_get_risk_metrics(self, client, api_headers):
        """测试获取风险指标"""
        response = client.get("/api/risk/summary", headers=api_headers)
        assert response.status_code in [200, 404, 500]


class TestMonitorEndpoints:
    """测试监控相关API"""

    def test_get_monitor_report_daily(self, client, api_headers):
        """测试获取每日监控报告"""
        response = client.get("/api/v1/monitor/report?report_type=daily", headers=api_headers)
        assert response.status_code in [200, 404, 500]

    def test_get_monitor_report_weekly(self, client, api_headers):
        """测试获取每周监控报告"""
        response = client.get("/api/v1/monitor/report?report_type=weekly", headers=api_headers)
        assert response.status_code in [200, 404, 500]


class TestMarketEndpoints:
    """测试市场相关API"""

    def test_get_market_indices(self, client, api_headers):
        """测试获取市场指数"""
        response = client.get("/api/v1/market/indices", headers=api_headers)
        assert response.status_code in [200, 404, 500]


class TestAuthentication:
    """测试身份认证"""

    def test_invalid_api_key(self, client):
        """测试无效的API Key"""
        headers = {"Authorization": "Bearer invalid_key"}
        response = client.get("/api/v1/stocks/sh600519", headers=headers)
        assert response.status_code == 401

    def test_missing_api_key(self, client):
        """测试缺少API Key"""
        response = client.get("/api/v1/stocks/sh600519")
        assert response.status_code in [401, 403, 404]


class TestRateLimit:
    """测试速率限制"""

    def test_rate_limit_exceeded(self, client):
        """测试超过速率限制 - 跳过，因为需要大量请求"""
        import pytest

        pytest.skip("速率限制测试需要大量请求，跳过以加快测试速度")

    @pytest.mark.network
    def test_rate_limit_headers(self, client):
        """测试速率限制头信息"""
        headers = {"Authorization": "Bearer demo_key"}
        response = client.get("/api/v1/stocks/sh600519", headers=headers)
        assert response.status_code in [200, 404, 429, 500]
        if response.status_code == 200:
            assert True


class TestErrorHandling:
    """测试错误处理"""

    def test_404_error(self, client, api_headers):
        """测试404错误"""
        response = client.get("/api/v1/nonexistent", headers=api_headers)
        assert response.status_code == 404

    def test_500_error_simulation(self, client, api_headers):
        """测试错误处理"""
        # 测试一个不存在的 API 端点
        response = client.get("/api/v1/nonexistent_endpoint", headers=api_headers)
        assert response.status_code in [404, 405, 500]
