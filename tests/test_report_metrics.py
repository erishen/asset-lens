"""
Tests for report metrics module.
报告指标模块测试
"""

from decimal import Decimal
from unittest.mock import MagicMock


class TestCalculateTotalReturn:
    """计算总收益率测试"""

    def test_calculate_total_return_positive(self):
        """测试正收益"""
        from asset_lens.report.metrics import calculate_total_return

        portfolio = MagicMock()
        portfolio.total_initial = Decimal("10000")
        portfolio.total_value = Decimal("12000")
        result = calculate_total_return(portfolio)
        assert result == Decimal("20")

    def test_calculate_total_return_negative(self):
        """测试负收益"""
        from asset_lens.report.metrics import calculate_total_return

        portfolio = MagicMock()
        portfolio.total_initial = Decimal("10000")
        portfolio.total_value = Decimal("8000")
        result = calculate_total_return(portfolio)
        assert result == Decimal("-20")

    def test_calculate_total_return_zero_initial(self):
        """测试初始值为零"""
        from asset_lens.report.metrics import calculate_total_return

        portfolio = MagicMock()
        portfolio.total_initial = Decimal("0")
        portfolio.total_value = Decimal("1000")
        result = calculate_total_return(portfolio)
        assert result == Decimal("0")


class TestCalculateAverageReturn:
    """计算平均收益率测试"""

    def test_calculate_average_return_normal(self):
        """测试正常计算"""
        from asset_lens.report.metrics import calculate_average_return

        portfolio = MagicMock()
        product1 = MagicMock()
        product1.annualized_return_irr = Decimal("10")
        product2 = MagicMock()
        product2.annualized_return_irr = Decimal("20")
        portfolio.products = [product1, product2]
        result = calculate_average_return(portfolio)
        assert result == Decimal("15")

    def test_calculate_average_return_empty(self):
        """测试空产品列表"""
        from asset_lens.report.metrics import calculate_average_return

        portfolio = MagicMock()
        portfolio.products = []
        result = calculate_average_return(portfolio)
        assert result == Decimal("0")

    def test_calculate_average_return_none_values(self):
        """测试 None 值"""
        from asset_lens.report.metrics import calculate_average_return

        portfolio = MagicMock()
        product1 = MagicMock()
        product1.annualized_return_irr = None
        product2 = MagicMock()
        product2.annualized_return_irr = Decimal("10")
        portfolio.products = [product1, product2]
        result = calculate_average_return(portfolio)
        assert result == Decimal("5")


class TestCalculatePositiveAvgReturn:
    """计算正收益产品平均收益率测试"""

    def test_positive_avg_return_normal(self):
        """测试正常计算"""
        from asset_lens.report.metrics import calculate_positive_avg_return

        portfolio = MagicMock()
        product1 = MagicMock()
        product1.annualized_return_irr = Decimal("10")
        product2 = MagicMock()
        product2.annualized_return_irr = Decimal("-5")
        product3 = MagicMock()
        product3.annualized_return_irr = Decimal("20")
        portfolio.products = [product1, product2, product3]
        result = calculate_positive_avg_return(portfolio)
        assert result == "15.00%"

    def test_positive_avg_return_no_positive(self):
        """测试没有正收益产品"""
        from asset_lens.report.metrics import calculate_positive_avg_return

        portfolio = MagicMock()
        product1 = MagicMock()
        product1.annualized_return_irr = Decimal("-5")
        product2 = MagicMock()
        product2.annualized_return_irr = Decimal("-10")
        portfolio.products = [product1, product2]
        result = calculate_positive_avg_return(portfolio)
        assert result == "0.00%"


class TestCalculateWeightedReturn:
    """计算加权收益率测试"""

    def test_weighted_return_normal(self):
        """测试正常计算"""
        from asset_lens.report.metrics import calculate_weighted_return

        portfolio = MagicMock()
        portfolio.total_initial = Decimal("10000")
        product1 = MagicMock()
        product1.initial_amount = Decimal("6000")
        product1.annualized_return_irr = Decimal("10")
        product2 = MagicMock()
        product2.initial_amount = Decimal("4000")
        product2.annualized_return_irr = Decimal("20")
        portfolio.products = [product1, product2]
        result = calculate_weighted_return(portfolio)
        assert result == Decimal("14")

    def test_weighted_return_zero_initial(self):
        """测试初始值为零"""
        from asset_lens.report.metrics import calculate_weighted_return

        portfolio = MagicMock()
        portfolio.total_initial = Decimal("0")
        portfolio.products = []
        result = calculate_weighted_return(portfolio)
        assert result == Decimal("0")


class TestCalculateInvestmentEfficiency:
    """计算投资效率指标测试"""

    def test_investment_efficiency_normal(self):
        """测试正常计算"""
        from asset_lens.report.metrics import calculate_investment_efficiency

        portfolio = MagicMock()
        product1 = MagicMock()
        product1.annualized_return_irr = Decimal("10")
        product1.investment_days = 100
        product2 = MagicMock()
        product2.annualized_return_irr = Decimal("-5")
        product2.investment_days = 200
        portfolio.products = [product1, product2]
        result = calculate_investment_efficiency(portfolio)
        assert result["efficiency_score"] == 50.0
        assert result["profit_rate"] == "1/2"
        assert result["avg_holding_days"] == 150.0

    def test_investment_efficiency_empty(self):
        """测试空产品列表"""
        from asset_lens.report.metrics import calculate_investment_efficiency

        portfolio = MagicMock()
        portfolio.products = []
        result = calculate_investment_efficiency(portfolio)
        assert result["efficiency_score"] == 0
        assert result["profit_rate"] == 0
        assert result["avg_holding_days"] == 0


class TestGetReturnDistribution:
    """获取收益率分布测试"""

    def test_return_distribution_all_categories(self):
        """测试所有类别"""
        from asset_lens.report.metrics import get_return_distribution

        portfolio = MagicMock()
        products = []
        for ret in [15, 5, -5, -15]:
            p = MagicMock()
            p.annualized_return_irr = Decimal(str(ret))
            products.append(p)
        portfolio.products = products
        result = get_return_distribution(portfolio)
        assert result["high_return"] == 1
        assert result["medium_return"] == 1
        assert result["low_return"] == 1
        assert result["loss"] == 1


class TestCalculateRiskScore:
    """计算风险评分测试"""

    def test_risk_score_normal(self):
        """测试正常计算"""
        from asset_lens.report.metrics import calculate_risk_score

        portfolio = MagicMock()
        product1 = MagicMock()
        product1.risk_level = "low"
        product2 = MagicMock()
        product2.risk_level = "high"
        portfolio.products = [product1, product2]
        result = calculate_risk_score(portfolio)
        assert result == 2.0

    def test_risk_score_empty(self):
        """测试空产品列表"""
        from asset_lens.report.metrics import calculate_risk_score

        portfolio = MagicMock()
        portfolio.products = []
        result = calculate_risk_score(portfolio)
        assert result == 0.0

    def test_risk_score_enum_value(self):
        """测试枚举值"""
        from asset_lens.report.metrics import calculate_risk_score

        portfolio = MagicMock()
        product = MagicMock()
        risk_level = MagicMock()
        risk_level.value = "medium"
        product.risk_level = risk_level
        portfolio.products = [product]
        result = calculate_risk_score(portfolio)
        assert result == 2.0


class TestGetTypeDistribution:
    """获取投资类型分布测试"""

    def test_type_distribution_normal(self):
        """测试正常计算"""
        from asset_lens.report.metrics import get_type_distribution

        portfolio = MagicMock()
        product1 = MagicMock()
        product1.investment_type = "基金"
        product1.current_amount = Decimal("10000")
        product1.initial_amount = Decimal("8000")
        product2 = MagicMock()
        product2.investment_type = "股票"
        product2.current_amount = Decimal("5000")
        product2.initial_amount = Decimal("4000")
        portfolio.products = [product1, product2]
        result = get_type_distribution(portfolio)
        assert "基金" in result
        assert "股票" in result
        assert result["基金"]["count"] == 1

    def test_type_distribution_enum_value(self):
        """测试枚举值"""
        from asset_lens.report.metrics import get_type_distribution

        portfolio = MagicMock()
        product = MagicMock()
        investment_type = MagicMock()
        investment_type.value = "基金"
        product.investment_type = investment_type
        product.current_amount = Decimal("10000")
        product.initial_amount = Decimal("8000")
        portfolio.products = [product]
        result = get_type_distribution(portfolio)
        assert "基金" in result


class TestGetRiskDistribution:
    """获取风险等级分布测试"""

    def test_risk_distribution_normal(self):
        """测试正常计算"""
        from asset_lens.report.metrics import get_risk_distribution

        portfolio = MagicMock()
        product1 = MagicMock()
        product1.risk_level = "低"
        product2 = MagicMock()
        product2.risk_level = "高"
        portfolio.products = [product1, product2]
        result = get_risk_distribution(portfolio)
        assert "低" in result
        assert "高" in result
        assert result["低"]["count"] == 1

    def test_risk_distribution_enum_value(self):
        """测试枚举值"""
        from asset_lens.report.metrics import get_risk_distribution

        portfolio = MagicMock()
        product = MagicMock()
        risk_level = MagicMock()
        risk_level.value = "中"
        product.risk_level = risk_level
        portfolio.products = [product]
        result = get_risk_distribution(portfolio)
        assert "中" in result
