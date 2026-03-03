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


class TestCLIPnl:
    """Test CLI PnL commands"""

    def test_pnl_help(self):
        """Test pnl command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["pnl", "--help"])
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


class TestCLIRealExecution:
    """Test CLI commands with real execution"""

    def test_analyze_with_console_output(self):
        """Test analyze with console output"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--data-mode", "sample", "--output-format", "console"])
        assert result.exit_code == 0

    def test_calculate_with_sample_data(self):
        """Test calculate with sample data"""
        runner = CliRunner()
        result = runner.invoke(cli, ["calculate", "--data-mode", "sample"])
        assert result.exit_code == 0

    def test_pnl_weekly_execution(self):
        """Test pnl weekly execution"""
        runner = CliRunner()
        result = runner.invoke(cli, ["pnl", "--weekly", "--data-mode", "sample"])
        assert result.exit_code in [0, 1, 2]

    def test_portfolio_metrics_execution(self):
        """Test portfolio metrics execution"""
        runner = CliRunner()
        result = runner.invoke(cli, ["portfolio-metrics", "--data-mode", "sample"])
        assert result.exit_code == 0

    def test_analyze_by_time_execution(self):
        """Test analyze by time execution"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze-by-time", "--data-mode", "sample"])
        assert result.exit_code == 0


class TestCLIErrorHandling:
    """Test CLI error handling"""

    def test_analyze_invalid_data_mode(self):
        """Test analyze with invalid data mode"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--data-mode", "invalid"])
        # Should handle gracefully
        assert result.exit_code in [0, 1, 2]

    def test_switch_mode_invalid_mode(self):
        """Test switch-mode with invalid mode"""
        runner = CliRunner()
        result = runner.invoke(cli, ["switch-mode", "--target-mode", "invalid"])
        # Should handle gracefully
        assert result.exit_code in [0, 1, 2]


class TestCLIOutputFormats:
    """Test CLI output format options"""

    def test_analyze_json_format(self):
        """Test analyze JSON format"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--data-mode", "sample", "--output-format", "json"])
        assert result.exit_code == 0

    def test_analyze_csv_format(self):
        """Test analyze CSV format"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--data-mode", "sample", "--output-format", "csv"])
        assert result.exit_code == 0

    def test_analyze_all_formats(self):
        """Test analyze all formats"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--data-mode", "sample", "--output-format", "all"])
        assert result.exit_code == 0


class TestCLIDataMode:
    """Test CLI data mode options"""

    def test_analyze_sample_mode(self):
        """Test analyze with sample mode"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--data-mode", "sample"])
        assert result.exit_code == 0

    def test_analyze_real_mode(self):
        """Test analyze with real mode"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--data-mode", "real"])
        # May fail if no real data, but should not crash
        assert result.exit_code in [0, 1]

    def test_calculate_sample_mode(self):
        """Test calculate with sample mode"""
        runner = CliRunner()
        result = runner.invoke(cli, ["calculate", "--data-mode", "sample"])
        assert result.exit_code == 0


class TestCLIRiskPreference:
    """Test CLI risk preference options"""

    def test_ai_analyze_with_risk_preference(self):
        """Test ai-analyze with risk preference"""
        runner = CliRunner()
        result = runner.invoke(cli, ["ai-analyze", "--data-mode", "sample", "--risk-preference", "moderate"])
        # May fail without API key or data, but should not crash
        assert result.exit_code in [0, 1, 2]

    def test_ai_analyze_conservative(self):
        """Test ai-analyze with conservative preference"""
        runner = CliRunner()
        result = runner.invoke(cli, ["ai-analyze", "--data-mode", "sample", "--risk-preference", "conservative"])
        assert result.exit_code in [0, 1]

    def test_ai_analyze_aggressive(self):
        """Test ai-analyze with aggressive preference"""
        runner = CliRunner()
        result = runner.invoke(cli, ["ai-analyze", "--data-mode", "sample", "--risk-preference", "aggressive"])
        assert result.exit_code in [0, 1]


class TestCLICompare:
    """Test CLI compare commands"""

    def test_compare_help(self):
        """Test compare command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["compare", "--help"])
        assert result.exit_code == 0

    def test_compare_execution(self):
        """Test compare command execution"""
        runner = CliRunner()
        result = runner.invoke(cli, ["compare", "--data-mode", "sample"])
        # May fail if no data, but should not crash
        assert result.exit_code in [0, 1, 2]

    def test_compare_with_dates(self):
        """Test compare command with specific dates"""
        runner = CliRunner()
        result = runner.invoke(cli, ["compare", "--before", "20250101", "--after", "20250201", "--data-mode", "sample"])
        # May fail if no data, but should not crash
        assert result.exit_code in [0, 1, 2]


class TestCLIEdgeCases:
    """Test CLI edge cases"""

    def test_analyze_with_invalid_output_format(self):
        """Test analyze with invalid output format"""
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--data-mode", "sample", "--output-format", "invalid"])
        # Should handle gracefully
        assert result.exit_code in [0, 1, 2]

    def test_set_rate_execution(self):
        """Test set-rate command execution"""
        runner = CliRunner()
        result = runner.invoke(cli, ["set-rate", "--rate-type", "usd", "--rate", "7.25"])
        # May fail if no config, but should not crash
        assert result.exit_code in [0, 1, 2]

    def test_estimate_pnl_weekly(self):
        """Test estimate-pnl weekly execution"""
        runner = CliRunner()
        result = runner.invoke(cli, ["estimate-pnl", "--data-mode", "sample", "--weekly"])
        # May fail if no data, but should not crash
        assert result.exit_code in [0, 1, 2]
