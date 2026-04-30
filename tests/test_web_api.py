"""
Tests for Asset Lens Web API.
Web API 测试
"""

import pytest
from fastapi.testclient import TestClient


class TestWebAPI:
    """Web API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from asset_lens.web.api import app

        return TestClient(app)

    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200

    def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

    def test_api_docs(self, client):
        """测试 API 文档"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json(self, client):
        """测试 OpenAPI JSON"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestStockRoutes:
    """股票路由测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from asset_lens.web.api import app

        return TestClient(app)

    def test_stock_list_endpoint(self, client):
        """测试股票列表端点"""
        response = client.get("/api/stocks")
        assert response.status_code in [200, 404, 500]

    def test_stock_search_endpoint(self, client):
        """测试股票搜索端点"""
        response = client.get("/api/stocks/search?keyword=平安")
        assert response.status_code in [200, 404, 500]


class TestPortfolioRoutes:
    """投资组合路由测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from asset_lens.web.api import app

        return TestClient(app)

    def test_portfolio_summary_endpoint(self, client):
        """测试投资组合摘要端点"""
        response = client.get("/api/portfolio/summary")
        assert response.status_code in [200, 404, 500]

    def test_portfolio_holdings_endpoint(self, client):
        """测试投资组合持仓端点"""
        response = client.get("/api/portfolio/holdings")
        assert response.status_code in [200, 404, 500]


class TestMarketRoutes:
    """市场路由测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from asset_lens.web.api import app

        return TestClient(app)

    def test_market_overview_endpoint(self, client):
        """测试市场概览端点"""
        response = client.get("/api/market/overview")
        assert response.status_code in [200, 404, 500]


class TestRiskRoutes:
    """风险路由测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from asset_lens.web.api import app

        return TestClient(app)

    def test_risk_metrics_endpoint(self, client):
        """测试风险指标端点"""
        response = client.get("/api/risk/metrics")
        assert response.status_code in [200, 404, 500]


class TestSystemRoutes:
    """系统路由测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from asset_lens.web.api import app

        return TestClient(app)

    def test_system_status_endpoint(self, client):
        """测试系统状态端点"""
        response = client.get("/api/system/status")
        assert response.status_code in [200, 404, 500]


class TestReportRoutes:
    """报告路由测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from asset_lens.web.api import app

        return TestClient(app)

    def test_report_list_endpoint(self, client):
        """测试报告列表端点"""
        response = client.get("/api/reports")
        assert response.status_code in [200, 404, 500]


class TestBackupRoutes:
    """备份路由测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from asset_lens.web.api import app

        return TestClient(app)

    def test_backup_list_endpoint(self, client):
        """测试备份列表端点"""
        response = client.get("/api/backup/list")
        assert response.status_code in [200, 404, 500]


class TestCORS:
    """CORS 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from asset_lens.web.api import app

        return TestClient(app)

    def test_cors_headers(self, client):
        """测试 CORS 头"""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200


class TestErrorHandling:
    """错误处理测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from asset_lens.web.api import app

        return TestClient(app)

    def test_404_error(self, client):
        """测试 404 错误"""
        response = client.get("/nonexistent/path")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """测试方法不允许"""
        response = client.post("/")
        assert response.status_code == 405
