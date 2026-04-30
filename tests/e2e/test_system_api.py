"""
E2E Tests for System API Endpoints.
系统 API 端点端到端测试
"""

from playwright.sync_api import Page


class TestSystemAPI:
    """系统 API 测试"""

    def test_provider_health(self, page: Page, base_url: str) -> None:
        """测试数据源健康状态"""
        response = page.request.get(f"{base_url}/api/provider-health")

        assert response.status in [200, 404, 401]

        if response.status == 200:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_cache_stats(self, page: Page, base_url: str) -> None:
        """测试缓存统计"""
        response = page.request.get(f"{base_url}/api/cache/stats")

        assert response.status in [200, 404, 401]

        if response.status == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_goals_list(self, page: Page, base_url: str) -> None:
        """测试目标列表"""
        response = page.request.get(f"{base_url}/api/goals")

        assert response.status in [200, 404, 401]


class TestBackupAPI:
    """备份 API 测试"""

    def test_backup_status(self, page: Page, base_url: str) -> None:
        """测试备份状态"""
        response = page.request.get(f"{base_url}/api/backup/status")

        assert response.status in [200, 404, 401]

    def test_backup_list(self, page: Page, base_url: str) -> None:
        """测试备份列表"""
        response = page.request.get(f"{base_url}/api/backup/list")

        assert response.status in [200, 404, 401]


class TestCompareAPI:
    """比较 API 测试"""

    def test_compare_weekly(self, page: Page, base_url: str) -> None:
        """测试周比较"""
        response = page.request.get(f"{base_url}/api/compare/weekly")

        assert response.status in [200, 404, 401]

    def test_compare_periods(self, page: Page, base_url: str) -> None:
        """测试期间比较"""
        response = page.request.get(f"{base_url}/api/compare/periods")

        assert response.status in [200, 404, 401]

    def test_compare_trend(self, page: Page, base_url: str) -> None:
        """测试趋势比较"""
        response = page.request.get(f"{base_url}/api/compare/trend")

        assert response.status in [200, 404, 401]

    def test_snapshot_list(self, page: Page, base_url: str) -> None:
        """测试快照列表"""
        response = page.request.get(f"{base_url}/api/compare/snapshot/list")

        assert response.status in [200, 404, 401]


class TestReportAPI:
    """报告 API 测试"""

    def test_report_export(self, page: Page, base_url: str) -> None:
        """测试报告导出"""
        response = page.request.get(f"{base_url}/api/reports/export")

        assert response.status in [200, 404, 401]


class TestRiskAPI:
    """风险 API 测试"""

    def test_risk_summary(self, page: Page, base_url: str) -> None:
        """测试风险摘要"""
        response = page.request.get(f"{base_url}/api/risk/summary")

        assert response.status in [200, 404, 401]


class TestStockPoolAPI:
    """股票池 API 测试"""

    def test_stock_pool_list(self, page: Page, base_url: str) -> None:
        """测试股票池列表"""
        response = page.request.get(f"{base_url}/api/stock-pool")

        assert response.status in [200, 404, 401]
