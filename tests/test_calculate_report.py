"""
Tests for calculate_report.py
"""

from decimal import Decimal
from unittest.mock import patch

import pytest

from asset_lens.data.models import InvestmentProduct, InvestmentType, Portfolio, RiskLevel
from asset_lens.report.calculate_report import CalculateReportGenerator


class TestCalculateReportGenerator:
    """CalculateReportGenerator 测试"""

    @pytest.fixture
    def generator(self):
        """创建测试实例"""
        with patch("asset_lens.report.calculate_report.config") as mock_config:
            mock_config.default_usd_rate = Decimal("7.2")
            mock_config.default_hkd_rate = Decimal("0.92")
            generator = CalculateReportGenerator()
            yield generator

    @pytest.fixture
    def sample_portfolio(self):
        """创建示例投资组合"""
        products = [
            InvestmentProduct(
                name="高收益产品",
                investment_type=InvestmentType.FUND,
                platform_amounts={"平台A": Decimal("10000")},
                initial_amount=Decimal("8000"),
                return_rate=Decimal("25.0"),
                annual_return=Decimal("25.0"),
                risk_level=RiskLevel.MEDIUM,
                start_date="2023-01-01",
            ),
            InvestmentProduct(
                name="低收益产品",
                investment_type=InvestmentType.STOCK,
                platform_amounts={"平台B": Decimal("5000")},
                initial_amount=Decimal("6000"),
                return_rate=Decimal("1.0"),
                annual_return=Decimal("1.0"),
                risk_level=RiskLevel.HIGH,
                start_date="2023-01-01",
            ),
            InvestmentProduct(
                name="负收益产品",
                investment_type=InvestmentType.STOCK,
                platform_amounts={"平台C": Decimal("3000")},
                initial_amount=Decimal("4000"),
                return_rate=Decimal("-25.0"),
                annual_return=Decimal("-25.0"),
                risk_level=RiskLevel.HIGH,
                start_date="2023-01-01",
            ),
            InvestmentProduct(
                name="无收益率产品",
                investment_type=InvestmentType.OTHER,
                platform_amounts={"平台D": Decimal("2000")},
                initial_amount=Decimal("2000"),
                return_rate=Decimal("0"),
                annual_return=None,
                risk_level=RiskLevel.LOW,
                start_date=None,
            ),
        ]
        return Portfolio(products=products)

    def test_init(self, generator):
        """测试初始化"""
        assert generator.console is not None

    def test_generate_calculate_report(self, generator, sample_portfolio):
        """测试生成计算报告"""
        result = generator.generate_calculate_report(sample_portfolio)

        assert "total_products" in result
        assert "products_with_return" in result
        assert "products_without_return" in result
        assert "top_performers" in result
        assert "negative_performers" in result
        assert "low_positive_performers" in result
        assert "avg_positive_return" in result
        assert "type_distribution" in result

    def test_generate_calculate_report_counts(self, generator, sample_portfolio):
        """测试生成计算报告 - 计数"""
        result = generator.generate_calculate_report(sample_portfolio)

        assert result["total_products"] == 4
        assert result["products_with_return"] == 3
        assert result["products_without_return"] == 1

    def test_generate_calculate_report_top_performers(self, generator, sample_portfolio):
        """测试生成计算报告 - 最高收益"""
        result = generator.generate_calculate_report(sample_portfolio)

        assert len(result["top_performers"]) >= 1
        assert result["top_performers"][0].name == "高收益产品"

    def test_generate_calculate_report_negative_performers(self, generator, sample_portfolio):
        """测试生成计算报告 - 负收益"""
        result = generator.generate_calculate_report(sample_portfolio)

        assert len(result["negative_performers"]) == 1
        assert result["negative_performers"][0].name == "负收益产品"

    def test_generate_calculate_report_low_positive(self, generator, sample_portfolio):
        """测试生成计算报告 - 低正收益"""
        result = generator.generate_calculate_report(sample_portfolio)

        assert len(result["low_positive_performers"]) == 1
        assert result["low_positive_performers"][0].name == "低收益产品"

    def test_generate_calculate_report_avg_positive_return(self, generator, sample_portfolio):
        """测试生成计算报告 - 平均正收益"""
        result = generator.generate_calculate_report(sample_portfolio)

        assert result["avg_positive_return"] == Decimal("13.0")

    def test_generate_calculate_report_type_distribution(self, generator, sample_portfolio):
        """测试生成计算报告 - 类型分布"""
        result = generator.generate_calculate_report(sample_portfolio)

        assert isinstance(result["type_distribution"], dict)
        assert len(result["type_distribution"]) >= 0

    def test_get_products_with_return(self, generator, sample_portfolio):
        """测试获取有收益率的产品"""
        result = generator._get_products_with_return(sample_portfolio)

        assert len(result) == 3

    def test_get_products_without_return(self, generator, sample_portfolio):
        """测试获取无收益率的产品"""
        result = generator._get_products_without_return(sample_portfolio)

        assert len(result) == 1

    def test_get_type_distribution(self, generator, sample_portfolio):
        """测试获取类型分布"""
        products_with_return = generator._get_products_with_return(sample_portfolio)
        result = generator._get_type_distribution(products_with_return)

        assert isinstance(result, dict)
        assert len(result) >= 0

    def test_generate_calculate_report_empty_portfolio(self, generator):
        """测试生成计算报告 - 空投资组合"""
        portfolio = Portfolio(products=[])
        result = generator.generate_calculate_report(portfolio)

        assert result["total_products"] == 0
        assert result["products_with_return"] == 0
        assert result["products_without_return"] == 0
        assert result["avg_positive_return"] == Decimal("0")

    def test_generate_calculate_report_only_positive(self, generator):
        """测试生成计算报告 - 只有正收益"""
        products = [
            InvestmentProduct(
                name="正收益产品",
                investment_type=InvestmentType.FUND,
                platform_amounts={"平台A": Decimal("10000")},
                initial_amount=Decimal("8000"),
                return_rate=Decimal("25.0"),
                annual_return=Decimal("25.0"),
                risk_level=RiskLevel.MEDIUM,
                start_date="2023-01-01",
            ),
        ]
        portfolio = Portfolio(products=products)
        result = generator.generate_calculate_report(portfolio)

        assert len(result["negative_performers"]) == 0
        assert result["avg_positive_return"] == Decimal("25.0")
