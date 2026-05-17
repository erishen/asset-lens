"""
Tests for analyze-sold and personal-irr commands
测试已卖出投资分析和个人财务IRR分析命令
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from datetime import date
from decimal import Decimal

from asset_lens.cli import cli
from asset_lens.data.models import SellRecord, RiskLevel


class TestAnalyzeSoldCommand:
    """测试 analyze-sold 命令"""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器"""
        return CliRunner()

    def test_analyze_sold_no_records(self, runner):
        """测试没有卖出记录的情况"""
        with patch("asset_lens.data.sell_record_parser.SellRecordParser.load_sell_records") as mock_load:
            mock_load.return_value = []
            result = runner.invoke(cli, ["analyze-sold"])
            assert result.exit_code == 0
            assert "没有已卖出的产品" in result.output

    def test_analyze_sold_with_records(self, runner):
        """测试有卖出记录的情况"""
        mock_records = [
            SellRecord(
                sell_date=date(2024, 12, 31),
                name="测试产品1",
                risk_level=RiskLevel.MEDIUM,
                initial_amount=Decimal("10000"),
                profit_amount=Decimal("500"),
                return_rate=Decimal("5.0"),
                investment_days=365,
                annual_return=Decimal("5.0"),
            ),
            SellRecord(
                sell_date=date(2024, 12, 31),
                name="测试产品2",
                risk_level=RiskLevel.LOW,
                initial_amount=Decimal("20000"),
                profit_amount=Decimal("1000"),
                return_rate=Decimal("5.0"),
                investment_days=180,
                annual_return=Decimal("10.0"),
            ),
        ]

        with patch("asset_lens.data.sell_record_parser.SellRecordParser.load_sell_records") as mock_load:
            mock_load.return_value = mock_records
            result = runner.invoke(cli, ["analyze-sold"])
            assert result.exit_code == 0
            assert "找到 2 个已卖出产品" in result.output
            assert "总投入: ¥30,000" in result.output
            assert "总收益: ¥1,500" in result.output
            assert "平均持有天数" in result.output

    def test_analyze_sold_missing_data(self, runner):
        """测试数据缺失的情况"""
        mock_records = [
            SellRecord(
                sell_date=date(2024, 12, 31),
                name="测试产品1",
                risk_level=RiskLevel.MEDIUM,
                initial_amount=None,  # 缺失数据
                profit_amount=Decimal("500"),
                return_rate=Decimal("5.0"),
            ),
        ]

        with patch("asset_lens.data.sell_record_parser.SellRecordParser.load_sell_records") as mock_load:
            mock_load.return_value = mock_records
            result = runner.invoke(cli, ["analyze-sold"])
            assert result.exit_code == 0
            assert "数据不完整" in result.output

    def test_analyze_sold_calculate_annual_return(self, runner):
        """测试年化收益率计算"""
        mock_records = [
            SellRecord(
                sell_date=date(2024, 12, 31),
                name="测试产品1",
                risk_level=RiskLevel.MEDIUM,
                initial_amount=Decimal("10000"),
                profit_amount=Decimal("1000"),
                return_rate=Decimal("10.0"),
                investment_days=365,
                annual_return=None,  # 需要计算
            ),
        ]

        with patch("asset_lens.data.sell_record_parser.SellRecordParser.load_sell_records") as mock_load:
            mock_load.return_value = mock_records
            result = runner.invoke(cli, ["analyze-sold"])
            assert result.exit_code == 0
            # 表格列名可能被截断，所以检查实际数据
            assert "10.00%" in result.output  # 年化收益率数据

    def test_analyze_sold_holding_period_analysis(self, runner):
        """测试持有期分析"""
        mock_records = [
            SellRecord(
                sell_date=date(2024, 12, 31),
                name="短期产品",
                risk_level=RiskLevel.LOW,
                initial_amount=Decimal("10000"),
                profit_amount=Decimal("100"),
                return_rate=Decimal("1.0"),
                investment_days=60,  # 短期
            ),
            SellRecord(
                sell_date=date(2024, 12, 31),
                name="中期产品",
                risk_level=RiskLevel.MEDIUM,
                initial_amount=Decimal("10000"),
                profit_amount=Decimal("500"),
                return_rate=Decimal("5.0"),
                investment_days=180,  # 中期
            ),
            SellRecord(
                sell_date=date(2024, 12, 31),
                name="长期产品",
                risk_level=RiskLevel.HIGH,
                initial_amount=Decimal("10000"),
                profit_amount=Decimal("2000"),
                return_rate=Decimal("20.0"),
                investment_days=730,  # 长期
            ),
        ]

        with patch("asset_lens.data.sell_record_parser.SellRecordParser.load_sell_records") as mock_load:
            mock_load.return_value = mock_records
            result = runner.invoke(cli, ["analyze-sold"])
            assert result.exit_code == 0
            assert "短期投资(<90天)" in result.output
            assert "中期投资(90-365天)" in result.output
            assert "长期投资(>365天)" in result.output


class TestPersonalIRRCommand:
    """测试 personal-irr 命令"""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器"""
        return CliRunner()

    def test_personal_irr_default_params(self, runner):
        """测试默认参数"""
        with patch("asset_lens.data.csv_parser.CSVParser.load_data") as mock_load:
            mock_load.return_value = []
            with patch("asset_lens.cli_modules.cli.analyze._get_data_dir") as mock_dir:
                mock_dir.return_value = None
                result = runner.invoke(cli, ["personal-irr"])
                assert result.exit_code == 0
                assert "月工资（税后）: ¥24,000" in result.output
                assert "年终奖" in result.output

    def test_personal_irr_custom_params(self, runner):
        """测试自定义参数"""
        with patch("asset_lens.data.csv_parser.CSVParser.load_data") as mock_load:
            mock_load.return_value = []
            with patch("asset_lens.cli_modules.cli.analyze._get_data_dir") as mock_dir:
                mock_dir.return_value = None
                result = runner.invoke(cli, ["personal-irr", "--monthly-salary", "30000", "--annual-bonus", "50000"])
                assert result.exit_code == 0
                assert "月工资（税后）: ¥30,000" in result.output
                assert "年终奖: ¥50,000" in result.output

    def test_personal_irr_assumptions_display(self, runner):
        """测试假设条件显示"""
        with patch("asset_lens.data.csv_parser.CSVParser.load_data") as mock_load:
            mock_load.return_value = []
            with patch("asset_lens.cli_modules.cli.analyze._get_data_dir") as mock_dir:
                mock_dir.return_value = None
                result = runner.invoke(cli, ["personal-irr"])
                assert result.exit_code == 0
                assert "假设条件:" in result.output
                assert "工资发放日: 每月15日" in result.output
                assert "年终奖发放日: 每年12月25日" in result.output

    def test_personal_irr_data_integrity_check(self, runner):
        """测试数据完整性检查"""
        mock_products = [
            MagicMock(
                name="产品1",
                transaction_records="2024-01-01,买入,10000",
                start_date=date(2024, 1, 1),
                current_amount=Decimal("11000"),
                initial_amount=Decimal("10000"),
            ),
            MagicMock(
                name="产品2",
                transaction_records=None,
                start_date=None,
                current_amount=Decimal("5000"),
                initial_amount=Decimal("5000"),
            ),
        ]

        with patch("asset_lens.data.csv_parser.CSVParser.load_data") as mock_load:
            mock_load.return_value = mock_products
            with patch("asset_lens.cli_modules.cli.analyze._get_data_dir") as mock_dir:
                mock_dir.return_value = None
                result = runner.invoke(cli, ["personal-irr"])
                assert result.exit_code == 0
                assert "数据完整性:" in result.output
                assert "总产品数: 2" in result.output

    def test_personal_irr_missing_consumption_data(self, runner):
        """测试消费数据缺失的情况"""
        with patch("asset_lens.data.csv_parser.CSVParser.load_data") as mock_load:
            mock_load.return_value = []
            with patch("asset_lens.cli_modules.cli.analyze._get_data_dir") as mock_dir:
                mock_dir.return_value = None
                result = runner.invoke(cli, ["personal-irr"])
                assert result.exit_code == 0
                assert "消费数据缺失" in result.output or "未找到" in result.output

    def test_personal_irr_with_estimated_consumption(self, runner):
        """测试有推算消费数据的情况"""
        with patch("asset_lens.data.csv_parser.CSVParser.load_data") as mock_load:
            mock_load.return_value = []
            with patch("asset_lens.cli_modules.cli.analyze._get_data_dir") as mock_dir:
                mock_dir.return_value = None
                result = runner.invoke(cli, ["personal-irr"])
                assert result.exit_code == 0
                # 检查是否有推算提示
                if "推算" in result.output:
                    assert "可能不准确" in result.output or "建议补充" in result.output

    def test_personal_irr_irr_warnings(self, runner):
        """测试IRR计算的警告信息"""
        with patch("asset_lens.data.csv_parser.CSVParser.load_data") as mock_load:
            mock_load.return_value = []
            with patch("asset_lens.cli_modules.cli.analyze._get_data_dir") as mock_dir:
                mock_dir.return_value = None
                result = runner.invoke(cli, ["personal-irr"])
                assert result.exit_code == 0
                # 检查是否有注意事项
                if "IRR 年化收益率" in result.output:
                    assert "注意事项:" in result.output
                    assert "基于假设条件" in result.output


class TestAnalyzeSoldEdgeCases:
    """测试 analyze-sold 边界情况"""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器"""
        return CliRunner()

    def test_analyze_sold_zero_initial_amount(self, runner):
        """测试初始金额为0的情况"""
        mock_records = [
            SellRecord(
                sell_date=date(2024, 12, 31),
                name="测试产品",
                risk_level=RiskLevel.MEDIUM,
                initial_amount=Decimal("0"),
                profit_amount=Decimal("0"),
                return_rate=Decimal("0"),
            ),
        ]

        with patch("asset_lens.data.sell_record_parser.SellRecordParser.load_sell_records") as mock_load:
            mock_load.return_value = mock_records
            result = runner.invoke(cli, ["analyze-sold"])
            assert result.exit_code == 0
            assert "数据不完整" in result.output

    def test_analyze_sold_negative_profit(self, runner):
        """测试收益为负的情况"""
        mock_records = [
            SellRecord(
                sell_date=date(2024, 12, 31),
                name="亏损产品",
                risk_level=RiskLevel.HIGH,
                initial_amount=Decimal("10000"),
                profit_amount=Decimal("-1000"),
                return_rate=Decimal("-10.0"),
                investment_days=365,
            ),
        ]

        with patch("asset_lens.data.sell_record_parser.SellRecordParser.load_sell_records") as mock_load:
            mock_load.return_value = mock_records
            result = runner.invoke(cli, ["analyze-sold"])
            assert result.exit_code == 0
            assert "¥-1,000" in result.output

    def test_analyze_sold_zero_investment_days(self, runner):
        """测试投资天数为0的情况"""
        mock_records = [
            SellRecord(
                sell_date=date(2024, 12, 31),
                name="测试产品",
                risk_level=RiskLevel.MEDIUM,
                initial_amount=Decimal("10000"),
                profit_amount=Decimal("100"),
                return_rate=Decimal("1.0"),
                investment_days=0,
                start_date=date(2024, 12, 31),  # 同一天买入卖出
            ),
        ]

        with patch("asset_lens.data.sell_record_parser.SellRecordParser.load_sell_records") as mock_load:
            mock_load.return_value = mock_records
            result = runner.invoke(cli, ["analyze-sold"])
            assert result.exit_code == 0
            # 应该能正确处理天数为0的情况


class TestPersonalIRREdgeCases:
    """测试 personal-irr 边界情况"""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器"""
        return CliRunner()

    def test_personal_irr_zero_salary(self, runner):
        """测试工资为0的情况"""
        with patch("asset_lens.data.csv_parser.CSVParser.load_data") as mock_load:
            mock_load.return_value = []
            with patch("asset_lens.cli_modules.cli.analyze._get_data_dir") as mock_dir:
                mock_dir.return_value = None
                result = runner.invoke(cli, ["personal-irr", "--monthly-salary", "0", "--annual-bonus", "0"])
                assert result.exit_code == 0
                assert "月工资（税后）: ¥0" in result.output

    def test_personal_irr_negative_net_income(self, runner):
        """测试净收入为负的情况"""
        with patch("asset_lens.data.csv_parser.CSVParser.load_data") as mock_load:
            mock_load.return_value = []
            with patch("asset_lens.cli_modules.cli.analyze._get_data_dir") as mock_dir:
                mock_dir.return_value = None
                # 设置很低的工资，高消费推算
                result = runner.invoke(cli, ["personal-irr", "--monthly-salary", "1000"])
                assert result.exit_code == 0

    def test_personal_irr_file_not_found(self, runner):
        """测试文件未找到的情况"""
        with patch("asset_lens.data.csv_parser.CSVParser.load_data") as mock_load:
            mock_load.side_effect = FileNotFoundError("测试文件未找到")
            result = runner.invoke(cli, ["personal-irr"])
            assert result.exit_code == 0
            assert "文件未找到" in result.output or "分析失败" in result.output
