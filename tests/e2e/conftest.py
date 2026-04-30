"""
Playwright E2E Tests Configuration.
E2E 测试配置

功能：
1. 失败时自动截图
2. 失败时保存 HTML 快照
3. 服务健康检查
4. 测试辅助工具
5. 性能优化
"""

import os
import time
from pathlib import Path

import pytest
import requests
from playwright.sync_api import BrowserContext, Page

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8000")
SCREENSHOT_DIR = Path("test-results/screenshots")
VIDEO_DIR = Path("test-results/videos")
TRACE_DIR = Path("test-results/traces")


def check_server_health(base_url: str, timeout: int = 3) -> bool:
    """检查服务器是否运行"""
    try:
        response = requests.get(f"{base_url}/", timeout=timeout)
        return response.status_code in [200, 404]
    except Exception:
        return False


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """浏览器上下文配置 - 性能优化"""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
        "record_video_dir": str(VIDEO_DIR) if os.getenv("RECORD_VIDEO") else None,
    }


@pytest.fixture(scope="session")
def base_url() -> str:
    """基础 URL"""
    return BASE_URL


@pytest.fixture(scope="session", autouse=True)
def check_server(base_url: str) -> None:
    """检查服务器是否运行，未运行则跳过测试"""
    if not check_server_health(base_url):
        pytest.skip(f"服务器未运行: {base_url}，请先运行 'make web' 启动服务")


@pytest.fixture(autouse=True)
def setup_page(page: Page, request: pytest.FixtureRequest) -> Page:
    """页面设置 - 性能优化超时时间"""
    page.set_default_timeout(10000)
    page.set_default_navigation_timeout(20000)

    yield page

    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        _save_failure_artifacts(page, request)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """测试结果钩子 - 用于失败截图"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def _save_failure_artifacts(page: Page, request: pytest.FixtureRequest) -> None:
    """保存失败时的截图和 HTML"""
    test_name = request.node.name.replace("[", "_").replace("]", "_")
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    screenshot_path = SCREENSHOT_DIR / f"{test_name}_{timestamp}.png"
    html_path = SCREENSHOT_DIR / f"{test_name}_{timestamp}.html"

    try:
        page.screenshot(path=str(screenshot_path))
        print(f"\n📸 截图已保存: {screenshot_path}")
    except Exception as e:
        print(f"\n⚠️ 截图失败: {e}")

    try:
        html_content = page.content()
        html_path.write_text(html_content, encoding="utf-8")
        print(f"📄 HTML 已保存: {html_path}")
    except Exception as e:
        print(f"⚠️ HTML 保存失败: {e}")


_shared_context = None
_shared_page = None


@pytest.fixture(scope="module")
def shared_context(browser_type_launch_args: dict, browser_type: type) -> BrowserContext:
    """共享浏览器上下文（同一模块内共享）"""
    global _shared_context
    if _shared_context is None:
        browser = browser_type.launch(**browser_type_launch_args)
        _shared_context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            ignore_https_errors=True,
        )
    return _shared_context


@pytest.fixture(scope="module")
def shared_page(shared_context: BrowserContext) -> Page:
    """共享页面（同一模块内共享同一个标签页）"""
    global _shared_page
    if _shared_page is None:
        _shared_page = shared_context.new_page()
        _shared_page.set_default_timeout(10000)
        _shared_page.set_default_navigation_timeout(20000)
    return _shared_page


class APITester:
    """API 测试辅助类"""

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def get(self, endpoint: str, expected_status: list = None) -> dict:
        """发送 GET 请求并验证响应"""
        url = f"{self.base_url}{endpoint}"
        response = self.page.request.get(url)

        if expected_status:
            assert response.status in expected_status, f"期望状态码 {expected_status}，实际 {response.status}"

        try:
            return {"status": response.status, "data": response.json()}
        except Exception:
            return {"status": response.status, "data": None}

    def post(self, endpoint: str, data: dict = None, expected_status: list = None) -> dict:
        """发送 POST 请求并验证响应"""
        url = f"{self.base_url}{endpoint}"
        response = self.page.request.post(url, data=data)

        if expected_status:
            assert response.status in expected_status, f"期望状态码 {expected_status}，实际 {response.status}"

        try:
            return {"status": response.status, "data": response.json()}
        except Exception:
            return {"status": response.status, "data": None}


@pytest.fixture
def api_tester(page: Page, base_url: str) -> APITester:
    """API 测试辅助工具"""
    return APITester(page, base_url)


class PageHelper:
    """页面操作辅助类"""

    def __init__(self, page: Page):
        self.page = page

    def goto_fast(self, url: str) -> None:
        """快速导航 - 只等待 DOM 加载"""
        self.page.goto(url, wait_until="domcontentloaded")

    def goto_and_wait(self, url: str, timeout: int = 10000) -> None:
        """导航到页面并等待加载完成"""
        self.page.goto(url, timeout=timeout)
        self.page.wait_for_load_state("domcontentloaded")

    def wait_for_text(self, text: str, timeout: int = 5000) -> None:
        """等待文本出现"""
        self.page.wait_for_selector(f"text={text}", timeout=timeout)

    def click_and_wait(self, selector: str, timeout: int = 5000) -> None:
        """点击元素并等待响应"""
        self.page.click(selector, timeout=timeout)
        self.page.wait_for_load_state("domcontentloaded")

    def fill_and_submit(self, selector: str, value: str, submit_selector: str = None) -> None:
        """填充表单并提交"""
        self.page.fill(selector, value)
        if submit_selector:
            self.page.click(submit_selector)

    def take_screenshot(self, name: str) -> str:
        """截图"""
        screenshot_dir = Path("test-results/screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        path = screenshot_dir / f"{name}.png"
        self.page.screenshot(path=str(path))
        return str(path)


@pytest.fixture
def page_helper(page: Page) -> PageHelper:
    """页面操作辅助工具"""
    return PageHelper(page)
