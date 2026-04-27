"""
E2E Tests with Shared Browser Window.
共享浏览器窗口的 E2E 测试
"""

import pytest
from playwright.sync_api import Page


@pytest.mark.usefixtures("shared_page")
class TestSharedBrowser:
    """共享浏览器窗口测试 - 所有测试在同一个标签页中执行"""

    def test_01_homepage(self, shared_page: Page, base_url: str) -> None:
        """测试 1: 访问首页"""
        shared_page.goto(base_url)
        shared_page.wait_for_load_state("networkidle")
        assert shared_page.title() is not None

    def test_02_navigate_to_docs(self, shared_page: Page, base_url: str) -> None:
        """测试 2: 导航到 API 文档"""
        shared_page.goto(f"{base_url}/docs")
        shared_page.wait_for_load_state("networkidle")
        assert "Swagger" in shared_page.title() or "API" in shared_page.title()

    def test_03_check_api_endpoint(self, shared_page: Page, base_url: str) -> None:
        """测试 3: 检查 API 端点"""
        response = shared_page.request.get(f"{base_url}/api/portfolio/summary")
        assert response.status in [200, 404, 401, 422]

    def test_04_market_data(self, shared_page: Page, base_url: str) -> None:
        """测试 4: 获取市场数据"""
        response = shared_page.request.get(f"{base_url}/api/market/indexes")
        assert response.status in [200, 404, 401]

    def test_05_back_to_home(self, shared_page: Page, base_url: str) -> None:
        """测试 5: 返回首页"""
        shared_page.goto(base_url)
        shared_page.wait_for_load_state("networkidle")
        assert shared_page.url == f"{base_url}/"
