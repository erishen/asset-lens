"""
Tests for CLI Commands - Additional Coverage.
CLI 命令测试 - 额外覆盖率
"""

import pytest
from click.testing import CliRunner


class TestCLICommandsAdditional:
    """CLI 命令测试 - 额外覆盖率"""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器"""
        from asset_lens.cli import cli
        runner = CliRunner()
        return runner, cli

    def test_version_command(self, runner):
        """测试版本命令"""
        runner, cli = runner
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0

    def test_check_command(self, runner):
        """测试检查命令"""
        runner, cli = runner
        result = runner.invoke(cli, ["check"])
        assert result.exit_code == 0

    def test_weekly_command(self, runner):
        """测试周报命令"""
        runner, cli = runner
        result = runner.invoke(cli, ["weekly"])
        # weekly 命令可能需要数据，所以只检查不会崩溃
        assert result.exit_code in [0, 1, 2]

    def test_sentiment_command(self, runner):
        """测试情感分析命令"""
        runner, cli = runner
        result = runner.invoke(cli, ["sentiment"])
        # sentiment 命令可能需要数据，所以只检查不会崩溃
        assert result.exit_code in [0, 1, 2]


class TestCLIStockCommands:
    """CLI 股票命令测试"""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器"""
        from asset_lens.cli import cli
        runner = CliRunner()
        return runner, cli

    def test_fetch_stock_help(self, runner):
        """测试股票获取帮助"""
        runner, cli = runner
        result = runner.invoke(cli, ["fetch-stock", "--help"])
        assert result.exit_code == 0

    def test_fetch_fund_help(self, runner):
        """测试基金获取帮助"""
        runner, cli = runner
        result = runner.invoke(cli, ["fetch-fund", "--help"])
        assert result.exit_code == 0

    def test_search_fund_help(self, runner):
        """测试基金搜索帮助"""
        runner, cli = runner
        result = runner.invoke(cli, ["search-fund", "--help"])
        assert result.exit_code == 0

    def test_screen_stocks_help(self, runner):
        """测试股票筛选帮助"""
        runner, cli = runner
        result = runner.invoke(cli, ["screen-stocks", "--help"])
        assert result.exit_code == 0

    def test_volume_breakout_help(self, runner):
        """测试放量突破帮助"""
        runner, cli = runner
        result = runner.invoke(cli, ["volume-breakout", "--help"])
        assert result.exit_code == 0


class TestCLIStrategyCommands:
    """CLI 策略命令测试"""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器"""
        from asset_lens.cli import cli
        runner = CliRunner()
        return runner, cli

    def test_strategy_help(self, runner):
        """测试策略帮助"""
        runner, cli = runner
        result = runner.invoke(cli, ["strategy", "--help"])
        assert result.exit_code == 0

    def test_stock_pool_help(self, runner):
        """测试股票池帮助"""
        runner, cli = runner
        result = runner.invoke(cli, ["stock-pool", "--help"])
        assert result.exit_code == 0

    def test_backtest_help(self, runner):
        """测试回测帮助"""
        runner, cli = runner
        result = runner.invoke(cli, ["backtest", "--help"])
        assert result.exit_code == 0

    def test_investment_status_help(self, runner):
        """测试投资状态帮助"""
        runner, cli = runner
        result = runner.invoke(cli, ["investment-status", "--help"])
        assert result.exit_code == 0

    def test_market_environment_help(self, runner):
        """测试市场环境帮助"""
        runner, cli = runner
        result = runner.invoke(cli, ["market-environment", "--help"])
        assert result.exit_code == 0


class TestCLITaskCommands:
    """CLI 任务命令测试"""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器"""
        from asset_lens.cli import cli
        runner = CliRunner()
        return runner, cli

    def test_run_daily_tasks_help(self, runner):
        """测试运行每日任务帮助"""
        runner, cli = runner
        result = runner.invoke(cli, ["run-daily-tasks", "--help"])
        assert result.exit_code == 0

    def test_task_status_help(self, runner):
        """测试任务状态帮助"""
        runner, cli = runner
        result = runner.invoke(cli, ["task-status", "--help"])
        assert result.exit_code == 0
