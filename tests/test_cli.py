"""
Tests for CLI module.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile
import os

from asset_lens.cli import cli


class TestCLI:
    """Test CLI commands"""

    def test_cli_help(self):
        """Test CLI help command"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage" in result.output

    def test_version_command(self):
        """Test version command"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "asset-lens" in result.output or "1.0.0" in result.output

    def test_check_command(self):
        """Test check command"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

    def test_analyze_command_sample(self):
        """Test analyze command with sample mode"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--data-mode", "sample", "--output-format", "console"])
        assert result.exit_code == 0

    def test_calculate_command(self):
        """Test calculate command"""
        runner = CliRunner()
        result = runner.invoke(cli, ["calculate", "--data-mode", "sample"])
        assert result.exit_code == 0

    def test_analyze_sold_command(self):
        """Test analyze-sold command"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze-sold", "--data-mode", "sample"])
        assert result.exit_code == 0

    def test_analyze_by_time_command(self):
        """Test analyze-by-time command"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze-by-time", "--data-mode", "sample"])
        assert result.exit_code == 0

    def test_mode_switch_commands(self):
        """Test mode switch commands"""
        runner = CliRunner()
        
        result = runner.invoke(cli, ["switch-mode", "--target-mode", "sample"])
        assert result.exit_code == 0
        
        result = runner.invoke(cli, ["switch-mode", "--target-mode", "real"])
        assert result.exit_code == 0


class TestCLIAnalysis:
    """Test CLI analysis commands"""

    def test_analyze_output_json(self):
        """Test analyze command with JSON output"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--data-mode", "sample", "--output-format", "json"])
        assert result.exit_code == 0

    def test_analyze_output_csv(self):
        """Test analyze command with CSV output"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--data-mode", "sample", "--output-format", "csv"])
        assert result.exit_code == 0

    def test_analyze_output_all(self):
        """Test analyze command with all output formats"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--data-mode", "sample", "--output-format", "all"])
        assert result.exit_code == 0


class TestCLIAssetSummary:
    """Test CLI asset summary commands"""

    def test_show_asset_summary(self):
        """Test show-asset-summary command"""
        runner = CliRunner()
        result = runner.invoke(cli, ["show-asset-summary", "--data-mode", "sample"])
        assert result.exit_code == 0

    def test_export_asset_summary_csv(self):
        """Test export-asset-summary command with CSV format"""
        runner = CliRunner()
        result = runner.invoke(cli, ["export-asset-summary", "--data-mode", "sample", "--output-format", "csv"])
        assert result.exit_code == 0

    def test_export_asset_summary_json(self):
        """Test export-asset-summary command with JSON format"""
        runner = CliRunner()
        result = runner.invoke(cli, ["export-asset-summary", "--data-mode", "sample", "--output-format", "json"])
        assert result.exit_code == 0


class TestCLIExchangeRate:
    """Test CLI exchange rate commands"""

    def test_show_exchange_rate_history(self):
        """Test show-exchange-rate-history command"""
        runner = CliRunner()
        result = runner.invoke(cli, ["show-exchange-rate-history", "--data-mode", "sample"])
        assert result.exit_code == 0

    def test_export_exchange_rate_history_csv(self):
        """Test export-exchange-rate-history command with CSV format"""
        runner = CliRunner()
        result = runner.invoke(cli, ["export-exchange-rate-history", "--data-mode", "sample", "--output-format", "csv"])
        assert result.exit_code == 0


class TestCLISellRecords:
    """Test CLI sell records commands"""

    def test_show_sell_records(self):
        """Test show-sell-records command"""
        runner = CliRunner()
        result = runner.invoke(cli, ["show-sell-records", "--data-mode", "sample"])
        assert result.exit_code == 0

    def test_export_sell_records_csv(self):
        """Test export-sell-records command with CSV format"""
        runner = CliRunner()
        result = runner.invoke(cli, ["export-sell-records", "--data-mode", "sample", "--output-format", "csv"])
        assert result.exit_code == 0


class TestCLIMarketData:
    """Test CLI market data commands"""

    def test_update_market_data_help(self):
        """Test update-market-data command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["update-market-data", "--help"])
        assert result.exit_code == 0


class TestCLIPortfolioMetrics:
    """Test CLI portfolio metrics commands"""

    def test_portfolio_metrics_help(self):
        """Test portfolio-metrics command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["portfolio-metrics", "--help"])
        assert result.exit_code == 0


class TestCLIAIAnalyze:
    """Test CLI AI analyze commands"""

    def test_ai_analyze_help(self):
        """Test ai-analyze command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["ai-analyze", "--help"])
        assert result.exit_code == 0
        assert "risk-preference" in result.output


class TestCLIInit:
    """Test CLI init commands"""

    def test_init_help(self):
        """Test init command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--help"])
        assert result.exit_code == 0

    def test_init_sample_help(self):
        """Test init-sample command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["init-sample", "--help"])
        assert result.exit_code == 0


class TestCLIWeekly:
    """Test CLI weekly commands"""

    def test_weekly_report_help(self):
        """Test weekly-report command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["weekly-report", "--help"])
        assert result.exit_code == 0


class TestCLIEstimatePnL:
    """Test CLI estimate PnL commands"""

    def test_estimate_pnl_help(self):
        """Test estimate-pnl command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["estimate-pnl", "--help"])
        assert result.exit_code == 0


class TestCLISwitchMode:
    """Test CLI switch mode commands"""

    def test_switch_mode_help(self):
        """Test switch-mode command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["switch-mode", "--help"])
        assert result.exit_code == 0

    def test_switch_mode_to_sample(self):
        """Test switch-mode to sample"""
        runner = CliRunner()
        result = runner.invoke(cli, ["switch-mode", "--target-mode", "sample"])
        assert result.exit_code == 0

    def test_switch_mode_to_real(self):
        """Test switch-mode to real"""
        runner = CliRunner()
        result = runner.invoke(cli, ["switch-mode", "--target-mode", "real"])
        assert result.exit_code == 0


class TestCLIUpdateMarketData:
    """Test CLI update market data commands"""

    def test_update_market_data_help(self):
        """Test update-market-data command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["update-market-data", "--help"])
        assert result.exit_code == 0


class TestCLIInit:
    """Test CLI init commands"""

    def test_init_help(self):
        """Test init command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--help"])
        assert result.exit_code == 0

    def test_init_sample_help(self):
        """Test init-sample command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["init-sample", "--help"])
        assert result.exit_code == 0


class TestCLIShowCommands:
    """Test CLI show commands"""

    def test_show_config_help(self):
        """Test show-config command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["show-config", "--help"])
        assert result.exit_code == 0

    def test_show_asset_summary_help(self):
        """Test show-asset-summary command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["show-asset-summary", "--help"])
        assert result.exit_code == 0

    def test_show_exchange_rate_history_help(self):
        """Test show-exchange-rate-history command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["show-exchange-rate-history", "--help"])
        assert result.exit_code == 0

    def test_show_sell_records_help(self):
        """Test show-sell-records command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["show-sell-records", "--help"])
        assert result.exit_code == 0


class TestCLIExportCommands:
    """Test CLI export commands"""

    def test_export_asset_summary_help(self):
        """Test export-asset-summary command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["export-asset-summary", "--help"])
        assert result.exit_code == 0

    def test_export_exchange_rate_history_help(self):
        """Test export-exchange-rate-history command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["export-exchange-rate-history", "--help"])
        assert result.exit_code == 0

    def test_export_sell_records_help(self):
        """Test export-sell-records command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["export-sell-records", "--help"])
        assert result.exit_code == 0


class TestCLISetRate:
    """Test CLI set rate commands"""

    def test_set_rate_help(self):
        """Test set-rate command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["set-rate", "--help"])
        assert result.exit_code == 0
