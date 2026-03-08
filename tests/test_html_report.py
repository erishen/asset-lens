"""
Tests for report/html_report.py
"""

import tempfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from asset_lens.report.html_report import HTMLReportGenerator


class TestHTMLReportGenerator:
    """HTMLReportGenerator 测试"""

    @pytest.fixture
    def temp_output_dir(self):
        """临时输出目录"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def generator(self, temp_output_dir):
        """创建测试实例"""
        generator = HTMLReportGenerator(output_dir=temp_output_dir)
        yield generator

    def test_init(self, generator, temp_output_dir):
        """测试初始化"""
        assert generator.output_dir == temp_output_dir
        assert generator.output_dir.exists()

    def test_generate_investment_report_basic(self, generator):
        """测试生成投资报告 - 基础"""
        portfolio_data = {
            "total_value": 100000,
            "total_profit": 10000,
            "overall_return_rate": 11.1,
            "total_products": 10,
            "type_distribution": {
                "基金": {"total_value": 50000, "count": 5},
                "股票": {"total_value": 50000, "count": 5},
            },
            "risk_distribution": {
                "低": {"total_value": 30000, "count": 3},
                "中": {"total_value": 50000, "count": 5},
                "高": {"total_value": 20000, "count": 2},
            },
        }

        result = generator.generate_investment_report(portfolio_data)

        assert result.exists()
        assert result.suffix == ".html"

    def test_generate_investment_report_with_analysis(self, generator):
        """测试生成投资报告 - 带分析结果"""
        portfolio_data = {
            "total_value": 100000,
            "total_profit": 10000,
            "overall_return_rate": 11.1,
            "total_products": 10,
            "type_distribution": {},
            "risk_distribution": {},
        }

        analysis_result = {
            "recommendations": ["建议1", "建议2"],
            "risk_warnings": ["警告1"],
            "top_performers": [
                {"name": "产品A", "return_rate": 25.0},
            ],
        }

        result = generator.generate_investment_report(
            portfolio_data, analysis_result=analysis_result
        )

        assert result.exists()

    def test_generate_investment_report_with_charts(self, generator, temp_output_dir):
        """测试生成投资报告 - 带图表"""
        portfolio_data = {
            "total_value": 100000,
            "total_profit": 10000,
            "overall_return_rate": 11.1,
            "total_products": 10,
            "type_distribution": {},
            "risk_distribution": {},
        }

        chart_file = temp_output_dir / "test_chart.png"
        chart_file.write_bytes(b"fake image data")

        charts = {"asset_allocation": chart_file}

        result = generator.generate_investment_report(
            portfolio_data, charts=charts
        )

        assert result.exists()

    def test_generate_investment_report_custom_filename(self, generator):
        """测试生成投资报告 - 自定义文件名"""
        portfolio_data = {
            "total_value": 100000,
            "total_profit": 10000,
            "overall_return_rate": 11.1,
            "total_products": 10,
            "type_distribution": {},
            "risk_distribution": {},
        }

        result = generator.generate_investment_report(
            portfolio_data, filename="custom_report.html"
        )

        assert result.exists()
        assert result.name == "custom_report.html"

    def test_generate_html_content(self, generator):
        """测试生成 HTML 内容"""
        portfolio_data = {
            "total_value": 100000,
            "total_profit": 10000,
            "overall_return_rate": 11.1,
            "total_products": 10,
            "type_distribution": {
                "基金": {"total_value": 50000, "count": 5},
            },
            "risk_distribution": {
                "低": {"total_value": 30000, "count": 3},
            },
        }

        result = generator._generate_html_content(portfolio_data)

        assert isinstance(result, str)
        assert "投资组合分析报告" in result

    def test_generate_distribution_table(self, generator):
        """测试生成分布表格"""
        distribution = {
            "基金": {"total_value": 50000, "count": 5},
            "股票": {"total_value": 30000, "count": 3},
        }

        result = generator._generate_distribution_table(distribution, 80000, "资产类型")

        assert isinstance(result, str)
        assert "基金" in result
        assert "股票" in result

    def test_generate_distribution_table_empty(self, generator):
        """测试生成分布表格 - 空数据"""
        result = generator._generate_distribution_table({}, 0, "资产类型")

        assert isinstance(result, str)

    def test_generate_investment_report_empty_data(self, generator):
        """测试生成投资报告 - 空数据"""
        portfolio_data = {}

        result = generator.generate_investment_report(portfolio_data)

        assert result.exists()
