"""
E2E Tests using Helper Tools.
使用辅助工具的 E2E 测试示例
"""

import pytest
from playwright.sync_api import Page


class TestAPIWithHelper:
    """使用 APITester 辅助类的 API 测试"""

    def test_portfolio_api(self, api_tester) -> None:
        """测试投资组合 API - 使用辅助类"""
        result = api_tester.get("/api/portfolio/summary", expected_status=[200, 404, 401])
        
        if result["status"] == 200:
            data = result["data"]
            assert "total_assets" in data
            assert "total_profit" in data
            assert "position_count" in data

    def test_market_api(self, api_tester) -> None:
        """测试市场数据 API - 使用辅助类"""
        result = api_tester.get("/api/market/indexes", expected_status=[200, 404, 401])
        
        if result["status"] == 200:
            data = result["data"]
            assert isinstance(data, list)

    def test_strategies_api(self, api_tester) -> None:
        """测试策略 API - 使用辅助类"""
        result = api_tester.get("/api/strategies", expected_status=[200, 404, 401])
        
        if result["status"] == 200:
            data = result["data"]
            assert isinstance(data, list)

    def test_ml_status_api(self, api_tester) -> None:
        """测试 ML 状态 API - 使用辅助类"""
        result = api_tester.get("/api/ml/model/status", expected_status=[200, 404, 401])

    def test_risk_api(self, api_tester) -> None:
        """测试风险 API - 使用辅助类"""
        result = api_tester.get("/api/risk/summary", expected_status=[200, 404, 401])


class TestPageWithHelper:
    """使用 PageHelper 辅助类的页面测试"""

    def test_homepage_with_helper(self, page_helper, base_url: str) -> None:
        """测试首页 - 使用辅助类"""
        page_helper.goto_and_wait(base_url)
        page_helper.take_screenshot("homepage")

    def test_docs_page_with_helper(self, page_helper, base_url: str) -> None:
        """测试 API 文档页面 - 使用辅助类"""
        page_helper.goto_and_wait(f"{base_url}/docs")
        page_helper.take_screenshot("docs_page")

    def test_responsive_with_helper(self, page_helper, page: Page, base_url: str) -> None:
        """测试响应式布局 - 使用辅助类"""
        viewports = [
            ("desktop", 1280, 720),
            ("tablet", 768, 1024),
            ("mobile", 375, 667),
        ]
        
        for name, width, height in viewports:
            page.set_viewport_size({"width": width, "height": height})
            page_helper.goto_and_wait(base_url)
            page_helper.take_screenshot(f"responsive_{name}")
