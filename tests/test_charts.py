"""
Tests for report/charts.py
"""

import tempfile
from pathlib import Path

import pytest

from asset_lens.report.charts import ChartGenerator


class TestChartGenerator:
    """ChartGenerator 测试"""

    @pytest.fixture
    def temp_output_dir(self):
        """临时输出目录"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def generator(self, temp_output_dir):
        """创建测试实例"""
        generator = ChartGenerator(output_dir=temp_output_dir)
        yield generator

    def test_init(self, generator, temp_output_dir):
        """测试初始化"""
        assert generator.output_dir == temp_output_dir
        assert generator.output_dir.exists()

    def test_generate_all_charts_empty(self, generator):
        """测试生成所有图表 - 空数据"""
        result = generator.generate_all_charts({})

        assert result == {}

    def test_generate_all_charts_with_data(self, generator):
        """测试生成所有图表 - 有数据"""
        portfolio_data = {
            "type_distribution": {
                "基金": {"total_value": 50000, "count": 5},
                "股票": {"total_value": 30000, "count": 3},
            },
            "risk_distribution": {
                "低": {"total_value": 20000, "count": 2},
                "中": {"total_value": 40000, "count": 4},
            },
            "return_distribution": {
                "正收益": 6,
                "负收益": 2,
            },
            "monthly_returns": [
                {"month": "2024-01", "return": 5.0},
                {"month": "2024-02", "return": 3.0},
            ],
            "cumulative_returns": [
                {"date": "2024-01-31", "value": 5.0},
                {"date": "2024-02-29", "value": 8.0},
            ],
            "top_products": [
                {"name": "产品A", "return_rate": 25.0},
                {"name": "产品B", "return_rate": 20.0},
            ],
        }

        result = generator.generate_all_charts(portfolio_data)

        assert "asset_allocation" in result
        assert "risk_distribution" in result
        assert "return_distribution" in result

    def test_generate_all_charts_with_prefix(self, generator):
        """测试生成所有图表 - 带前缀"""
        portfolio_data = {
            "type_distribution": {
                "基金": {"total_value": 50000, "count": 5},
            },
        }

        result = generator.generate_all_charts(portfolio_data, prefix="test_")

        assert "asset_allocation" in result

    def test_generate_asset_allocation_chart(self, generator):
        """测试生成资产配置图表"""
        type_distribution = {
            "基金": {"total_value": 50000, "count": 5},
            "股票": {"total_value": 30000, "count": 3},
            "货币": {"total_value": 20000, "count": 2},
        }

        result = generator.generate_asset_allocation_chart(type_distribution)

        assert result.exists()
        assert result.suffix == ".png"

    def test_generate_risk_distribution_chart(self, generator):
        """测试生成风险分布图表"""
        risk_distribution = {
            "低": {"total_value": 20000, "count": 2},
            "中": {"total_value": 40000, "count": 4},
            "高": {"total_value": 20000, "count": 2},
        }

        result = generator.generate_risk_distribution_chart(risk_distribution)

        assert result.exists()
        assert result.suffix == ".png"

    def test_generate_return_distribution_chart(self, generator):
        """测试生成收益分布图表"""
        return_distribution = {
            "正收益": 6,
            "负收益": 2,
        }

        result = generator.generate_return_distribution_chart(return_distribution)

        assert result.exists()
        assert result.suffix == ".png"

    def test_generate_monthly_returns_chart(self, generator):
        """测试生成月度收益图表"""
        monthly_returns = [
            {"month": "2024-01", "return": 5.0},
            {"month": "2024-02", "return": 3.0},
            {"month": "2024-03", "return": -2.0},
        ]

        result = generator.generate_monthly_returns_chart(monthly_returns)

        assert result.exists()
        assert result.suffix == ".png"

    def test_generate_cumulative_returns_chart(self, generator):
        """测试生成累计收益图表"""
        cumulative_returns = [
            {"date": "2024-01-31", "value": 5.0},
            {"date": "2024-02-29", "value": 8.0},
            {"date": "2024-03-31", "value": 10.0},
        ]

        result = generator.generate_cumulative_returns_chart(cumulative_returns)

        assert result.exists()
        assert result.suffix == ".png"

    def test_generate_top_products_chart(self, generator):
        """测试生成最佳产品图表"""
        top_products = [
            {"name": "产品A", "return_rate": 25.0},
            {"name": "产品B", "return_rate": 20.0},
            {"name": "产品C", "return_rate": 15.0},
        ]

        result = generator.generate_top_products_chart(top_products)

        assert result.exists()
        assert result.suffix == ".png"

    def test_generate_custom_filename(self, generator):
        """测试自定义文件名"""
        type_distribution = {
            "基金": {"total_value": 50000, "count": 5},
        }

        result = generator.generate_asset_allocation_chart(type_distribution, filename="custom_chart.png")

        assert result.exists()
        assert result.name == "custom_chart.png"
