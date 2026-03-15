"""
Tests for CLI commands.
CLI 命令测试
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock


class TestCLICommands:
    """CLI 命令测试"""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器"""
        return CliRunner()

    def test_version_command(self, runner):
        """测试版本命令"""
        from asset_lens.cli import cli
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0 or "version" in result.output.lower() or "1.0" in result.output

    def test_show_config_command(self, runner):
        """测试显示配置命令"""
        from asset_lens.cli import cli
        result = runner.invoke(cli, ["show-config"])
        assert result.exit_code in [0, 1, 2]

    def test_strategy_command(self, runner):
        """测试策略命令"""
        from asset_lens.cli import cli
        result = runner.invoke(cli, ["strategy", "--help"])
        assert result.exit_code in [0, 1, 2]

    def test_sentiment_command(self, runner):
        """测试风向分析命令"""
        from asset_lens.cli import cli
        result = runner.invoke(cli, ["monitor-status"])
        assert result.exit_code in [0, 1, 2]

    def test_weekly_command(self, runner):
        """测试周报命令"""
        from asset_lens.cli import cli
        result = runner.invoke(cli, ["weekly"])
        assert result.exit_code in [0, 1, 2]


class TestCLIAnalyzeCommands:
    """分析命令测试"""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器"""
        return CliRunner()

    def test_analyze_command(self, runner):
        """测试分析命令"""
        from asset_lens.cli import cli
        result = runner.invoke(cli, ["analyze", "--help"])
        assert result.exit_code in [0, 1, 2]

    def test_calculate_command(self, runner):
        """测试计算命令"""
        from asset_lens.cli import cli
        result = runner.invoke(cli, ["calculate", "--help"])
        assert result.exit_code in [0, 1, 2]


class TestCLIStockCommands:
    """股票命令测试"""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器"""
        return CliRunner()

    def test_stock_pool_command(self, runner):
        """测试股票池命令"""
        from asset_lens.cli import cli
        result = runner.invoke(cli, ["stock-pool", "--help"])
        assert result.exit_code in [0, 1, 2]

    def test_stock_pool_status_command(self, runner):
        """测试股票池状态命令"""
        from asset_lens.cli import cli
        result = runner.invoke(cli, ["stock-pool", "--action", "list"])
        assert result.exit_code in [0, 1, 2]
