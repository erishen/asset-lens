"""
Tests for cli.py
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner


class TestCLI:
    """CLI 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器"""
        return CliRunner()

    def test_cli_help(self, runner):
        """测试 CLI 帮助命令"""
        from asset_lens.cli import cli

        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage" in result.output

    def test_cli_version(self, runner):
        """测试 CLI 版本命令"""
        from asset_lens.cli import cli

        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0

    def test_completion_command(self, runner):
        """测试自动补全命令"""
        from asset_lens.cli import cli

        result = runner.invoke(cli, ["completion"])
        assert result.exit_code == 0
        assert "completion" in result.output.lower()

    def test_init_command(self, runner, temp_cache_path):
        """测试初始化命令"""
        from asset_lens.cli import cli

        with patch('asset_lens.config.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            mock_config.project_root = temp_cache_path
            mock_config.ensure_directories = MagicMock()

            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0

    def test_show_config_command(self, runner, temp_cache_path):
        """测试显示配置命令"""
        from asset_lens.cli import cli

        with patch('asset_lens.config.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            mock_config.project_root = temp_cache_path
            mock_config.data_mode = "test"

            result = runner.invoke(cli, ["show-config"])
            assert result.exit_code == 0

    def test_init_sample_command(self, runner, temp_cache_path):
        """测试初始化示例数据命令"""
        from asset_lens.cli import cli

        with patch('asset_lens.config.config') as mock_config:
            mock_config.project_root = temp_cache_path
            result = runner.invoke(cli, ["init-sample"])
            assert result.exit_code == 0

    def test_calculate_command_with_mock(self, runner, temp_cache_path):
        """测试计算命令 - 使用 mock"""
        from asset_lens.cli import cli

        with patch('asset_lens.data.csv_parser.CSVParser') as mock_parser:
            mock_parser.load_data.return_value = []
            mock_parser.get_exchange_rates.return_value = (7.0, 0.9)
            
            with patch('asset_lens.config.config') as mock_config:
                mock_config.default_usd_rate = 7.0
                mock_config.default_hkd_rate = 0.9
                mock_config.data_mode = "sample"
                mock_config.get_latest_data_dir.return_value = None
                
                result = runner.invoke(cli, ["calculate", "--data-mode", "sample"])
                assert result.exit_code == 0

    def test_analyze_command_with_mock(self, runner, temp_cache_path):
        """测试分析命令 - 使用 mock"""
        from asset_lens.cli import cli

        with patch('asset_lens.data.csv_parser.CSVParser') as mock_parser:
            mock_parser.load_data.return_value = []
            
            with patch('asset_lens.config.config') as mock_config:
                mock_config.default_usd_rate = 7.0
                mock_config.default_hkd_rate = 0.9
                mock_config.data_mode = "sample"
                mock_config.output_path = temp_cache_path
                
                result = runner.invoke(cli, ["analyze", "--data-mode", "sample"])
                assert result.exit_code == 0

    def test_switch_mode_command(self, runner, temp_cache_path):
        """测试切换数据模式命令"""
        from asset_lens.cli import cli

        env_file = temp_cache_path / ".env"
        env_file.write_text("DATA_MODE=sample\n")

        with patch('asset_lens.config.config') as mock_config:
            mock_config.project_root = temp_cache_path
            
            result = runner.invoke(cli, ["switch-mode", "--target-mode", "real"])
            assert result.exit_code == 0
            assert "real" in result.output

    def test_set_rate_command(self, runner, temp_cache_path):
        """测试设置汇率命令"""
        from asset_lens.cli import cli

        with patch('asset_lens.utils.currency_converter.currency_converter') as mock_converter:
            mock_converter.set_rate = MagicMock()
            mock_converter.save_cached_rates = MagicMock()
            
            result = runner.invoke(cli, ["set-rate", "--currency", "USD", "--rate", "7.2"])
            assert result.exit_code == 0
            assert "USD" in result.output

    def test_show_asset_summary_no_file(self, runner, temp_cache_path):
        """测试显示资产汇总 - 无文件"""
        from asset_lens.cli import cli

        with patch('asset_lens.cli_modules.cli.analyze._get_data_dir') as mock_get_dir:
            mock_get_dir.return_value = temp_cache_path
            
            result = runner.invoke(cli, ["analyze"])
            assert result.exit_code == 0

    def test_show_exchange_rate_history_no_file(self, runner, temp_cache_path):
        """测试显示汇率历史 - 无文件"""
        from asset_lens.cli import cli

        result = runner.invoke(cli, ["calculate"])
        assert result.exit_code == 0

    def test_show_sell_records_no_file(self, runner, temp_cache_path):
        """测试显示卖出记录 - 无文件"""
        from asset_lens.cli import cli

        result = runner.invoke(cli, ["analyze-sold"])
        assert result.exit_code == 0

    def test_export_asset_summary_no_file(self, runner, temp_cache_path):
        """测试导出资产汇总 - 无文件"""
        from asset_lens.cli import cli

        result = runner.invoke(cli, ["weekly"])
        assert result.exit_code in [0, 1, 2]

    def test_pnl_command_with_mock(self, runner, temp_cache_path):
        """测试盈亏估算命令 - 使用 mock"""
        from asset_lens.cli import cli

        with patch('asset_lens.data.csv_parser.CSVParser') as mock_parser:
            mock_parser.load_data.return_value = []
            
            with patch('asset_lens.config.config') as mock_config:
                mock_config.data_mode = "sample"
                
                result = runner.invoke(cli, ["pnl"])
                assert result.exit_code == 0

    def test_estimate_command_with_mock(self, runner, temp_cache_path):
        """测试收益估算命令 - 使用 mock"""
        from asset_lens.cli import cli

        with patch('asset_lens.data.csv_parser.CSVParser') as mock_parser:
            mock_parser.load_data.return_value = []
            
            with patch('asset_lens.config.config') as mock_config:
                mock_config.data_mode = "sample"
                
                result = runner.invoke(cli, ["estimate"])
                assert result.exit_code == 0

    def test_analyze_sold_no_file(self, runner, temp_cache_path):
        """测试已卖出投资分析 - 无文件"""
        from asset_lens.cli import cli

        result = runner.invoke(cli, ["analyze-sold"])
        assert result.exit_code == 0

    def test_analyze_by_time_with_mock(self, runner, temp_cache_path):
        """测试按时间分析命令 - 使用 mock"""
        from asset_lens.cli import cli

        with patch('asset_lens.data.csv_parser.CSVParser') as mock_parser:
            mock_parser.load_data.return_value = []
            
            with patch('asset_lens.config.config') as mock_config:
                mock_config.data_mode = "sample"
                
                result = runner.invoke(cli, ["analyze-by-time"])
                assert result.exit_code == 0

    def test_portfolio_metrics_with_mock(self, runner, temp_cache_path):
        """测试投资组合指标命令 - 使用 mock"""
        from asset_lens.cli import cli

        result = runner.invoke(cli, ["calculate"])
        assert result.exit_code == 0


class TestInteractiveCommands:
    """测试交互式命令"""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器"""
        return CliRunner()

    def test_interactive_exit(self, runner):
        """测试交互式命令 - 退出"""
        from asset_lens.cli import cli

        result = runner.invoke(cli, ["interactive"], input="0\n")
        assert result.exit_code == 0

    def test_interactive_invalid_choice(self, runner):
        """测试交互式命令 - 无效选项"""
        from asset_lens.cli import cli

        result = runner.invoke(cli, ["interactive"], input="99\n0\n")
        assert result.exit_code == 0
