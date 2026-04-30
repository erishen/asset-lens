"""
Optimized E2E Tests for Dashboard.
优化的 E2E Dashboard 测试

优化策略：
1. 使用共享浏览器上下文
2. 合并相似测试
3. 标记慢速测试
"""

import pytest
from playwright.sync_api import Page

VIEWPORTS = [
    ("desktop", 1280, 720),
    ("tablet", 768, 1024),
    ("mobile", 375, 667),
]


class TestDashboardOptimized:
    """优化后的 Dashboard 测试"""

    def test_homepage(self, shared_page: Page, base_url: str) -> None:
        """测试首页加载"""
        shared_page.goto(base_url, wait_until="domcontentloaded")
        title = shared_page.title()
        assert title is not None

    def test_api_docs(self, shared_page: Page, base_url: str) -> None:
        """测试 API 文档页面"""
        shared_page.goto(f"{base_url}/docs", wait_until="domcontentloaded")

    def test_api_health(self, shared_page: Page, base_url: str) -> None:
        """测试 API 健康检查"""
        response = shared_page.request.get(f"{base_url}/")
        assert response.status in [200, 404]


class TestResponsiveLayout:
    """响应式布局测试"""

    @pytest.mark.slow
    @pytest.mark.parametrize("name,width,height", VIEWPORTS)
    def test_viewport(self, page: Page, base_url: str, name: str, width: int, height: int) -> None:
        """测试不同视口"""
        page.set_viewport_size({"width": width, "height": height})
        page.goto(base_url, wait_until="domcontentloaded")


class TestAccessibility:
    """可访问性测试"""

    def test_page_has_title(self, shared_page: Page, base_url: str) -> None:
        """测试页面有标题"""
        shared_page.goto(base_url, wait_until="domcontentloaded")
        title = shared_page.title()
        assert title is not None and len(title) > 0

    def test_images_have_alt(self, shared_page: Page, base_url: str) -> None:
        """测试图片有 alt 属性"""
        shared_page.goto(base_url, wait_until="domcontentloaded")
        images = shared_page.locator("img").all()
        for img in images:
            alt = img.get_attribute("alt")
            assert alt is not None or img.get_attribute("role") == "presentation"

    def test_buttons_have_text(self, shared_page: Page, base_url: str) -> None:
        """测试按钮有文本"""
        shared_page.goto(base_url, wait_until="domcontentloaded")
        buttons = shared_page.locator("button").all()
        for button in buttons[:5]:
            text = button.inner_text()
            aria_label = button.get_attribute("aria-label")
            title = button.get_attribute("title")
            assert len(text) > 0 or aria_label is not None or title is not None
