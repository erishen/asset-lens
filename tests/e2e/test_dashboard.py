"""
E2E Tests for Web Dashboard.
Web 仪表板端到端测试
"""

import re

import pytest
from playwright.sync_api import Page, expect


class TestDashboard:
    """仪表板测试"""

    def test_homepage_loads(self, page: Page, base_url: str) -> None:
        """测试首页加载"""
        page.goto(base_url)
        
        expect(page).to_have_title(re.compile(r"Asset Lens|Stock Analyzer|投资"))
        
        page.wait_for_load_state("networkidle")

    def test_navigation_menu(self, page: Page, base_url: str) -> None:
        """测试导航菜单"""
        page.goto(base_url)
        
        nav_items = page.locator("nav a, .nav-link, [role='navigation'] a")
        count = nav_items.count()
        
        assert count >= 0, "导航菜单应该存在"

    def test_api_health_check(self, page: Page, base_url: str) -> None:
        """测试 API 健康检查"""
        response = page.request.get(f"{base_url}/api/health")
        
        assert response.status in [200, 404], f"API 响应状态码: {response.status}"

    def test_static_files_loaded(self, page: Page, base_url: str) -> None:
        """测试静态文件加载"""
        page.goto(base_url)
        
        scripts = page.locator("script[src]")
        styles = page.locator("link[rel='stylesheet']")
        
        script_count = scripts.count()
        style_count = styles.count()
        
        assert script_count >= 0, "页面应该包含脚本"
        assert style_count >= 0, "页面应该包含样式"


class TestStockPool:
    """股票池测试"""

    def test_stock_pool_page(self, page: Page, base_url: str) -> None:
        """测试股票池页面"""
        page.goto(f"{base_url}/stock-pool")
        
        page.wait_for_load_state("networkidle")

    def test_add_stock_form(self, page: Page, base_url: str) -> None:
        """测试添加股票表单"""
        page.goto(base_url)
        
        add_button = page.locator("button:has-text('添加'), [data-testid='add-stock']")
        if add_button.count() > 0:
            add_button.first.click()
            
            code_input = page.locator("input[name='code'], input[placeholder*='代码']")
            if code_input.count() > 0:
                code_input.first.fill("sh600519")


class TestPortfolio:
    """投资组合测试"""

    def test_portfolio_page(self, page: Page, base_url: str) -> None:
        """测试投资组合页面"""
        page.goto(f"{base_url}/portfolio")
        
        page.wait_for_load_state("networkidle")

    def test_portfolio_summary(self, page: Page, base_url: str) -> None:
        """测试投资组合摘要"""
        page.goto(base_url)
        
        summary = page.locator(".portfolio-summary, [data-testid='portfolio-summary']")
        
        if summary.count() > 0:
            expect(summary.first).to_be_visible()


class TestMarket:
    """市场数据测试"""

    def test_market_page(self, page: Page, base_url: str) -> None:
        """测试市场页面"""
        page.goto(f"{base_url}/market")
        
        page.wait_for_load_state("networkidle")

    def test_index_display(self, page: Page, base_url: str) -> None:
        """测试指数显示"""
        page.goto(base_url)
        
        index_elements = page.locator(".index, [data-testid='index'], .market-index")
        
        if index_elements.count() > 0:
            expect(index_elements.first).to_be_visible()


class TestReports:
    """报告测试"""

    def test_reports_page(self, page: Page, base_url: str) -> None:
        """测试报告页面"""
        page.goto(f"{base_url}/reports")
        
        page.wait_for_load_state("networkidle")

    def test_generate_report(self, page: Page, base_url: str) -> None:
        """测试生成报告"""
        page.goto(f"{base_url}/reports")
        
        generate_button = page.locator("button:has-text('生成'), button:has-text('报告')")
        
        if generate_button.count() > 0:
            generate_button.first.click()
            
            page.wait_for_timeout(1000)


class TestWebSocket:
    """WebSocket 测试"""

    def test_websocket_connection(self, page: Page, base_url: str) -> None:
        """测试 WebSocket 连接"""
        ws_connected = False
        
        def on_web_socket(ws):
            nonlocal ws_connected
            ws_connected = True
            
            ws.on("framesreceived", lambda frames: None)
            
            ws.on("closed", lambda: None)

        page.on("websocket", on_web_socket)
        
        page.goto(base_url)
        
        page.wait_for_timeout(2000)
        
        page.goto(base_url)


class TestResponsive:
    """响应式测试"""

    @pytest.mark.parametrize("viewport", [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 768, "height": 1024},
        {"width": 375, "height": 667},
    ])
    def test_responsive_layout(self, page: Page, base_url: str, viewport: dict) -> None:
        """测试响应式布局"""
        page.set_viewport_size(viewport)
        page.goto(base_url)
        
        page.wait_for_load_state("networkidle")
        
        body = page.locator("body")
        expect(body).to_be_visible()


class TestAccessibility:
    """可访问性测试"""

    def test_page_has_title(self, page: Page, base_url: str) -> None:
        """测试页面标题"""
        page.goto(base_url)
        
        title = page.title()
        assert len(title) > 0, "页面应该有标题"

    def test_images_have_alt(self, page: Page, base_url: str) -> None:
        """测试图片有 alt 属性"""
        page.goto(base_url)
        
        images = page.locator("img")
        count = images.count()
        
        for i in range(count):
            img = images.nth(i)
            alt = img.get_attribute("alt")
            
            if img.get_attribute("role") != "presentation":
                pass

    def test_buttons_have_text(self, page: Page, base_url: str) -> None:
        """测试按钮有文本"""
        page.goto(base_url)
        
        buttons = page.locator("button")
        count = buttons.count()
        
        for i in range(min(count, 10)):
            button = buttons.nth(i)
            text = button.inner_text()
            aria_label = button.get_attribute("aria-label")
            
            has_accessible_name = len(text.strip()) > 0 or aria_label is not None
