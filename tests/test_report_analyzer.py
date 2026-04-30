"""
Tests for report/analyzer.py
"""

from decimal import Decimal
from unittest.mock import patch

import pytest

from asset_lens.data.models import InvestmentProduct, InvestmentType, Portfolio, RiskLevel
from asset_lens.report.analyzer import ReportGenerator


class TestReportGenerator:
    """ReportGenerator 测试"""

    @pytest.fixture
    def generator(self):
        """创建测试实例"""
        with patch("asset_lens.report.analyzer.config") as mock_config:
            mock_config.report_language = "zh"
            mock_config.data_mode = "test"
            mock_config.default_usd_rate = Decimal("7.2")
            mock_config.default_hkd_rate = Decimal("0.92")
            mock_config.min_return_threshold = Decimal("5.0")
            generator = ReportGenerator()
            yield generator

    @pytest.fixture
    def sample_portfolio(self):
        """创建示例投资组合"""
        products = [
            InvestmentProduct(
                name="测试产品A",
                investment_type=InvestmentType.FUND,
                platform_amounts={"平台A": Decimal("10000")},
                initial_amount=Decimal("8000"),
                return_rate=Decimal("25.0"),
                annual_return=Decimal("25.0"),
                risk_level=RiskLevel.MEDIUM,
            ),
            InvestmentProduct(
                name="测试产品B",
                investment_type=InvestmentType.STOCK,
                platform_amounts={"平台B": Decimal("5000")},
                initial_amount=Decimal("6000"),
                return_rate=Decimal("-16.67"),
                annual_return=Decimal("-16.67"),
                risk_level=RiskLevel.HIGH,
            ),
        ]
        return Portfolio(products=products)

    def test_init(self, generator):
        """测试初始化"""
        assert generator.report_language == "zh"
        assert generator.sold_analyzer is not None
        assert generator.time_analyzer is not None

    def test_get_exchange_rates(self, generator):
        """测试获取汇率"""
        result = generator.get_exchange_rates()

        assert "usd_rate" in result
        assert "hkd_rate" in result
        assert "source" in result

    def test_generate_portfolio_summary(self, generator, sample_portfolio):
        """测试生成投资组合摘要"""
        result = generator.generate_portfolio_summary(sample_portfolio)

        assert "total_products" in result
        assert "total_value" in result
        assert "total_initial" in result
        assert "total_profit" in result
        assert result["total_products"] == 2

    def test_get_top_performers(self, generator, sample_portfolio):
        """测试获取最高收益产品"""
        result = generator.get_top_performers(sample_portfolio, top_n=10)

        assert len(result) == 2
        assert result[0]["name"] == "测试产品A"

    def test_get_low_return_products(self, generator, sample_portfolio):
        """测试获取低收益产品"""
        result = generator.get_low_return_products(sample_portfolio, threshold=Decimal("0"))

        assert len(result) >= 1

    def test_get_type_distribution(self, generator, sample_portfolio):
        """测试获取类型分布"""
        result = generator.get_type_distribution(sample_portfolio)

        assert isinstance(result, dict)

    def test_get_risk_distribution(self, generator, sample_portfolio):
        """测试获取风险分布"""
        result = generator.get_risk_distribution(sample_portfolio)

        assert isinstance(result, dict)

    def test_generate_risk_warnings(self, generator, sample_portfolio):
        """测试生成风险警告"""
        result = generator.generate_risk_warnings(sample_portfolio)

        assert isinstance(result, list)

    def test_generate_investment_advice(self, generator, sample_portfolio):
        """测试生成投资建议"""
        result = generator.generate_investment_advice(sample_portfolio)

        assert isinstance(result, list)

    def test_generate_comprehensive_evaluation(self, generator, sample_portfolio):
        """测试生成综合评估"""
        result = generator.generate_comprehensive_evaluation(sample_portfolio)

        assert isinstance(result, dict)

    def test_generate_investment_efficiency(self, generator, sample_portfolio):
        """测试生成投资效率"""
        result = generator.generate_investment_efficiency(sample_portfolio)

        assert isinstance(result, dict)

    def test_get_short_term_observation_products(self, generator):
        """测试获取短期观察产品"""
        products = [
            InvestmentProduct(
                name="短期产品A",
                investment_type=InvestmentType.FUND,
                platform_amounts={"平台A": Decimal("10000")},
                initial_amount=Decimal("10000"),
                return_rate=Decimal("1.0"),
                annual_return=Decimal("2.0"),
                risk_level=RiskLevel.LOW,
            ),
        ]
        portfolio = Portfolio(products=products)

        result = generator.get_short_term_observation_products(portfolio)

        assert isinstance(result, list)

    def test_get_high_return_reference_products(self, generator):
        """测试获取高收益参考产品"""
        products = [
            InvestmentProduct(
                name="高收益产品A",
                investment_type=InvestmentType.FUND,
                platform_amounts={"平台A": Decimal("10000")},
                initial_amount=Decimal("8000"),
                return_rate=Decimal("50.0"),
                annual_return=Decimal("50.0"),
                risk_level=RiskLevel.HIGH,
            ),
        ]
        portfolio = Portfolio(products=products)

        result = generator.get_high_return_reference_products(portfolio)

        assert isinstance(result, list)
        assert len(result) >= 1

    def test_generate_time_group_analysis(self, generator, sample_portfolio):
        """测试生成时间分组分析"""
        result = generator.generate_time_group_analysis(sample_portfolio)

        assert "groups" in result
        assert "total_products" in result

    def test_generate_special_bonds_analysis(self, generator):
        """测试生成特别国债分析"""
        products = [
            InvestmentProduct(
                name="特别国债2024",
                investment_type=InvestmentType.BOND,
                platform_amounts={"银行": Decimal("10000")},
                initial_amount=Decimal("10000"),
                return_rate=Decimal("3.0"),
                annual_return=Decimal("3.0"),
                risk_level=RiskLevel.LOW,
            ),
        ]
        portfolio = Portfolio(products=products)

        result = generator.generate_special_bonds_analysis(portfolio)

        assert isinstance(result, list)
