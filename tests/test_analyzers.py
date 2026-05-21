"""
Tests for Analyzers Module.
分析器模块测试
"""

import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "asset_lens"))

from asset_lens.analyzers.evaluation_analyzer import EvaluationAnalyzer
from asset_lens.analyzers.portfolio_analyzer import LegacyPortfolioAnalyzer
from asset_lens.analyzers.risk_analyzer import LegacyRiskAnalyzer
from asset_lens.data.models import InvestmentProduct, InvestmentType, Portfolio, RiskLevel


@pytest.fixture
def sample_portfolio():
    """创建示例投资组合"""
    products = [
        InvestmentProduct(
            name="平安银行",
            investment_type=InvestmentType.STOCK,
            current_amount=Decimal("50000"),
            initial_amount=Decimal("45000"),
            profit_amount=Decimal("5000"),
            return_rate=Decimal("11.11"),
            annual_return=Decimal("12.5"),
            investment_days=365,
            risk_level=RiskLevel.MEDIUM,
            start_date="2023-01-01",
        ),
        InvestmentProduct(
            name="国债",
            investment_type=InvestmentType.BOND,
            current_amount=Decimal("30000"),
            initial_amount=Decimal("30000"),
            profit_amount=Decimal("0"),
            return_rate=Decimal("0"),
            annual_return=Decimal("2.5"),
            investment_days=180,
            risk_level=RiskLevel.LOW,
            start_date="2023-07-01",
        ),
        InvestmentProduct(
            name="亏损股票",
            investment_type=InvestmentType.STOCK,
            current_amount=Decimal("8000"),
            initial_amount=Decimal("10000"),
            profit_amount=Decimal("-2000"),
            return_rate=Decimal("-20.0"),
            annual_return=Decimal("-25.0"),
            investment_days=90,
            risk_level=RiskLevel.HIGH,
            start_date="2024-01-01",
        ),
    ]

    return Portfolio(products=products)


class TestEvaluationAnalyzer:
    """测试评估分析器"""

    def test_generate_comprehensive_evaluation(self, sample_portfolio):
        """测试生成综合评估"""
        analyzer = EvaluationAnalyzer()
        result = analyzer.generate_comprehensive_evaluation(sample_portfolio)

        assert "total_value" in result
        assert "total_profit" in result
        assert "return_rate" in result
        assert "time_weighted_return" in result
        assert "evaluation" in result
        assert "risk_level" in result
        assert "diversification_score" in result

    def test_calculate_time_weighted_return(self, sample_portfolio):
        """测试计算时间加权收益率"""
        analyzer = EvaluationAnalyzer()
        result = analyzer._calculate_time_weighted_return(sample_portfolio)

        assert isinstance(result, Decimal)

    def test_calculate_time_weighted_return_empty(self):
        """测试空投资组合的时间加权收益率"""
        analyzer = EvaluationAnalyzer()
        portfolio = Portfolio(products=[])

        result = analyzer._calculate_time_weighted_return(portfolio)

        assert result == Decimal("0")

    def test_get_evaluation_text_excellent(self):
        """测试优秀评估文本"""
        analyzer = EvaluationAnalyzer()

        result = analyzer._get_evaluation_text(Decimal("15"), Decimal("12"))

        assert "优秀" in result

    def test_get_evaluation_text_good(self):
        """测试良好评估文本"""
        analyzer = EvaluationAnalyzer()

        result = analyzer._get_evaluation_text(Decimal("6"), Decimal("5"))

        assert "良好" in result

    def test_get_evaluation_text_average(self):
        """测试一般评估文本"""
        analyzer = EvaluationAnalyzer()

        result = analyzer._get_evaluation_text(Decimal("3"), Decimal("2"))

        assert "一般" in result

    def test_get_evaluation_text_poor(self):
        """测试较差评估文本"""
        analyzer = EvaluationAnalyzer()

        result = analyzer._get_evaluation_text(Decimal("1"), Decimal("0.5"))

        assert "较差" in result

    def test_get_evaluation_text_loss(self):
        """测试亏损评估文本"""
        analyzer = EvaluationAnalyzer()

        result = analyzer._get_evaluation_text(Decimal("-5"), Decimal("-3"))

        assert "亏损" in result

    def test_get_risk_level(self, sample_portfolio):
        """测试获取风险等级"""
        analyzer = EvaluationAnalyzer()

        result = analyzer._get_risk_level(sample_portfolio)

        assert result is not None

    def test_calculate_diversification_score(self, sample_portfolio):
        """测试计算分散度评分"""
        analyzer = EvaluationAnalyzer()

        result = analyzer._calculate_diversification_score(sample_portfolio)

        assert isinstance(result, float)
        assert 0 <= result <= 100


class TestRiskAnalyzer:
    """测试风险分析器"""

    def test_generate_risk_warnings(self, sample_portfolio):
        """测试生成风险警告"""
        analyzer = LegacyRiskAnalyzer()
        warnings = analyzer.generate_risk_warnings(sample_portfolio)

        assert isinstance(warnings, list)

    def test_generate_risk_warnings_with_loss(self, sample_portfolio):
        """测试有亏损产品的风险警告"""
        analyzer = LegacyRiskAnalyzer()
        warnings = analyzer.generate_risk_warnings(sample_portfolio)

        loss_warnings = [w for w in warnings if w["type"] == "loss"]
        assert len(loss_warnings) > 0

    def test_generate_risk_warnings_empty_portfolio(self):
        """测试空投资组合的风险警告"""
        analyzer = LegacyRiskAnalyzer()
        portfolio = Portfolio(products=[])

        warnings = analyzer.generate_risk_warnings(portfolio)

        assert warnings == []

    def test_get_low_return_products(self, sample_portfolio):
        """测试获取低收益产品"""
        analyzer = LegacyRiskAnalyzer()

        low_return = analyzer._get_low_return_products(sample_portfolio, threshold=5.0)

        assert isinstance(low_return, list)


class TestPortfolioAnalyzer:
    """测试投资组合分析器"""

    def test_generate_portfolio_summary(self, sample_portfolio):
        """测试生成投资组合摘要"""
        analyzer = LegacyPortfolioAnalyzer()
        result = analyzer.generate_portfolio_summary(sample_portfolio)

        assert isinstance(result, dict)
        assert "total_products" in result
        assert "total_value" in result

    def test_get_top_performers(self, sample_portfolio):
        """测试获取最高收益产品"""
        analyzer = LegacyPortfolioAnalyzer()

        result = analyzer.get_top_performers(sample_portfolio)

        assert isinstance(result, list)

    def test_get_low_return_products(self, sample_portfolio):
        """测试获取低收益产品"""
        analyzer = LegacyPortfolioAnalyzer()

        result = analyzer.get_low_return_products(sample_portfolio)

        assert isinstance(result, list)

    def test_get_type_distribution(self, sample_portfolio):
        """测试获取投资类型分布"""
        analyzer = LegacyPortfolioAnalyzer()

        result = analyzer.get_type_distribution(sample_portfolio)

        assert isinstance(result, dict)

    def test_get_risk_distribution(self, sample_portfolio):
        """测试获取风险分布"""
        analyzer = LegacyPortfolioAnalyzer()

        result = analyzer.get_risk_distribution(sample_portfolio)

        assert isinstance(result, dict)
