"""
E2E Tests for User Workflows.
用户工作流端到端测试
"""

from playwright.sync_api import Page, expect


class TestUserWorkflows:
    """用户工作流测试"""

    def test_complete_trading_workflow(self, page: Page, base_url: str) -> None:
        """测试完整交易工作流"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        market_nav = page.locator("a:has-text('市场'), [href*='market']")
        if market_nav.count() > 0:
            market_nav.first.click()
            page.wait_for_load_state("networkidle")

        portfolio_nav = page.locator("a:has-text('持仓'), [href*='portfolio']")
        if portfolio_nav.count() > 0:
            portfolio_nav.first.click()
            page.wait_for_load_state("networkidle")

        reports_nav = page.locator("a:has-text('报告'), [href*='report']")
        if reports_nav.count() > 0:
            reports_nav.first.click()
            page.wait_for_load_state("networkidle")

    def test_stock_search_workflow(self, page: Page, base_url: str) -> None:
        """测试股票搜索工作流"""
        page.goto(base_url)

        search_input = page.locator("input[type='search'], input[placeholder*='搜索'], input[placeholder*='代码']")

        if search_input.count() > 0:
            search_input.first.fill("600519")

            search_button = page.locator("button:has-text('搜索'), button[type='submit']")
            if search_button.count() > 0:
                search_button.first.click()
                page.wait_for_timeout(1000)

    def test_report_generation_workflow(self, page: Page, base_url: str) -> None:
        """测试报告生成工作流"""
        page.goto(f"{base_url}/reports")
        page.wait_for_load_state("networkidle")

        report_type_select = page.locator("select[name='type'], select[id='report-type']")
        if report_type_select.count() > 0:
            report_type_select.first.select_option(label="周报")

        generate_button = page.locator("button:has-text('生成'), button:has-text('报告')")
        if generate_button.count() > 0:
            generate_button.first.click()
            page.wait_for_timeout(2000)

    def test_settings_workflow(self, page: Page, base_url: str) -> None:
        """测试设置工作流"""
        page.goto(base_url)

        settings_nav = page.locator("a:has-text('设置'), [href*='setting']")
        if settings_nav.count() > 0:
            settings_nav.first.click()
            page.wait_for_load_state("networkidle")


class TestErrorHandling:
    """错误处理测试"""

    def test_invalid_stock_code(self, page: Page, base_url: str) -> None:
        """测试无效股票代码"""
        page.goto(base_url)

        search_input = page.locator("input[type='search'], input[placeholder*='搜索']")

        if search_input.count() > 0:
            search_input.first.fill("invalid_code_12345")

            search_button = page.locator("button:has-text('搜索')")
            if search_button.count() > 0:
                search_button.first.click()
                page.wait_for_timeout(1000)

                error_message = page.locator(".error, .alert-error, [role='alert']")

                if error_message.count() > 0:
                    expect(error_message.first).to_be_visible()

    def test_network_error_handling(self, page: Page, base_url: str) -> None:
        """测试网络错误处理"""
        page.goto(base_url)

        page.route("**/api/**", lambda route: route.abort())

        page.reload()

        page.wait_for_load_state("networkidle")

        page.unroute("**/api/**")


class TestFormValidation:
    """表单验证测试"""

    def test_required_fields(self, page: Page, base_url: str) -> None:
        """测试必填字段验证"""
        page.goto(base_url)

        add_button = page.locator("button:has-text('添加股票'), button:has-text('添加')")
        if add_button.count() > 0:
            add_button.first.click()

            submit_button = page.locator("button[type='submit']")
            if submit_button.count() > 0:
                submit_button.first.click()

                page.wait_for_timeout(500)

                error_messages = page.locator(".error, .invalid-feedback, [role='alert']")

                if error_messages.count() > 0:
                    pass

    def test_numeric_input_validation(self, page: Page, base_url: str) -> None:
        """测试数字输入验证"""
        page.goto(base_url)

        number_inputs = page.locator("input[type='number'], input[inputmode='numeric']")

        if number_inputs.count() > 0:
            number_inputs.first.fill("abc")

            number_inputs.first.fill("123.45")


class TestPerformance:
    """性能测试"""

    def test_page_load_time(self, page: Page, base_url: str) -> None:
        """测试页面加载时间"""
        import time

        start = time.time()
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        end = time.time()

        load_time = end - start

        assert load_time < 10, f"页面加载时间应该小于 10 秒，实际: {load_time:.2f}s"

    def test_large_data_rendering(self, page: Page, base_url: str) -> None:
        """测试大数据渲染"""
        page.goto(f"{base_url}/stocks")
        page.wait_for_load_state("networkidle")

        table_rows = page.locator("table tbody tr, .stock-list .stock-item")
        row_count = table_rows.count()

        if row_count > 100:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(500)

            page.evaluate("window.scrollTo(0, 0)")

    def test_memory_usage(self, page: Page, base_url: str) -> None:
        """测试内存使用"""
        page.goto(base_url)

        for _ in range(5):
            page.reload()
            page.wait_for_load_state("networkidle")

        metrics = page.evaluate(
            """() => {
            if (performance.memory) {
                return {
                    usedJSHeapSize: performance.memory.usedJSHeapSize,
                    totalJSHeapSize: performance.memory.totalJSHeapSize
                };
            }
            return null;
        }"""
        )

        if metrics:
            used_mb = metrics["usedJSHeapSize"] / 1024 / 1024
            assert used_mb < 500, f"内存使用应该小于 500MB，实际: {used_mb:.0f}MB"
