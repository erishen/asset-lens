"""
Tests for CLI Registration.
CLI 命令注册验证测试 - 确保所有命令正确注册
"""


class TestCLIRegistration:
    """CLI 命令注册验证测试"""

    def test_cli_module_import(self):
        """测试 CLI 模块可以正确导入"""
        from asset_lens.cli import cli, create_cli

        assert cli is not None
        assert create_cli is not None

    def test_cli_has_commands(self):
        """测试 CLI 有注册命令"""
        from asset_lens.cli import cli

        commands = cli.list_commands(None)
        assert len(commands) > 0, "CLI 应该有注册的命令"

    def test_core_commands_registered(self):
        """测试核心命令已注册"""
        from asset_lens.cli import cli

        commands = cli.list_commands(None)

        core_commands = ["version", "check", "init", "show-config"]
        for cmd in core_commands:
            assert cmd in commands, f"核心命令 {cmd} 应该已注册"

    def test_data_commands_registered(self):
        """测试数据命令已注册"""
        from asset_lens.cli import cli

        commands = cli.list_commands(None)

        data_commands = ["fetch-stock", "fetch-fund", "search-fund", "update-market-data"]
        for cmd in data_commands:
            assert cmd in commands, f"数据命令 {cmd} 应该已注册"

    def test_analyze_commands_registered(self):
        """测试分析命令已注册"""
        from asset_lens.cli import cli

        commands = cli.list_commands(None)

        analyze_commands = ["analyze", "calculate", "pnl", "estimate"]
        for cmd in analyze_commands:
            assert cmd in commands, f"分析命令 {cmd} 应该已注册"

    def test_strategy_commands_registered(self):
        """测试策略命令已注册"""
        from asset_lens.cli import cli

        commands = cli.list_commands(None)

        strategy_commands = ["strategy", "backtest", "screen-stocks"]
        for cmd in strategy_commands:
            assert cmd in commands, f"策略命令 {cmd} 应该已注册"

    def test_report_commands_registered(self):
        """测试报告命令已注册"""
        from asset_lens.cli import cli

        commands = cli.list_commands(None)

        report_commands = ["weekly", "monthly", "daily-report"]
        for cmd in report_commands:
            assert cmd in commands, f"报告命令 {cmd} 应该已注册"

    def test_stock_pool_commands_registered(self):
        """测试股票池命令已注册"""
        from asset_lens.cli import cli

        commands = cli.list_commands(None)

        stock_pool_commands = ["stock-pool", "track-stocks"]
        for cmd in stock_pool_commands:
            assert cmd in commands, f"股票池命令 {cmd} 应该已注册"

    def test_monitor_commands_registered(self):
        """测试监控命令已注册"""
        from asset_lens.cli import cli

        commands = cli.list_commands(None)

        monitor_commands = ["run-daily-tasks", "market-environment"]
        for cmd in monitor_commands:
            assert cmd in commands, f"监控命令 {cmd} 应该已注册"

    def test_provider_commands_registered(self):
        """测试 Provider Registry 命令已注册"""
        from asset_lens.cli import cli

        commands = cli.list_commands(None)

        provider_commands = ["provider-info", "fetch-unified", "provider-health", "cache-stats", "cache-clear"]
        for cmd in provider_commands:
            assert cmd in commands, f"Provider 命令 {cmd} 应该已注册"

    def test_command_count(self):
        """测试命令数量在合理范围"""
        from asset_lens.cli import cli

        commands = cli.list_commands(None)

        # 应该有 40-75 个命令
        assert len(commands) >= 40, f"命令数量 {len(commands)} 应该 >= 40"
        assert len(commands) <= 75, f"命令数量 {len(commands)} 应该 <= 75"

    def test_no_duplicate_commands(self):
        """测试没有重复的命令"""
        from asset_lens.cli import cli

        commands = cli.list_commands(None)

        # 检查没有重复
        assert len(commands) == len(set(commands)), "不应该有重复的命令"

    def test_cli_main_entry(self):
        """测试 CLI 主入口"""
        from asset_lens.__main__ import cli as main_cli

        assert main_cli is not None

    def test_cli_module_main_entry(self):
        """测试 CLI 模块的 __main__ 入口"""
        from asset_lens.cli_modules.cli.__main__ import cli as module_cli

        assert module_cli is not None
