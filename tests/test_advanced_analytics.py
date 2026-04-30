"""
Tests for advanced analytics.
"""

from datetime import date
from decimal import Decimal

from asset_lens.core.advanced_analytics import (
    AdvancedAnalytics,
    DrawdownResult,
    SharpeResult,
    VolatilityResult,
    advanced_analytics,
)
from asset_lens.data.models import InvestmentProduct, InvestmentType, Portfolio, RiskLevel


class TestDrawdownResult:
    """Test DrawdownResult dataclass"""

    def test_drawdown_result_creation(self):
        result = DrawdownResult(
            max_drawdown=Decimal("1000"),
            max_drawdown_percent=Decimal("10"),
            peak_date=date(2024, 1, 1),
            trough_date=date(2024, 2, 1),
            recovery_date=date(2024, 3, 1),
            drawdown_duration=30,
        )
        assert result.max_drawdown == Decimal("1000")
        assert result.max_drawdown_percent == Decimal("10")

    def test_drawdown_result_to_dict(self):
        result = DrawdownResult(
            max_drawdown=Decimal("1000"),
            max_drawdown_percent=Decimal("10"),
            peak_date=date(2024, 1, 1),
            trough_date=date(2024, 2, 1),
            recovery_date=date(2024, 3, 1),
            drawdown_duration=30,
        )
        d = result.to_dict()
        assert d["最大回撤金额"] == "1000"
        assert d["最大回撤比例"] == "10.00%"


class TestSharpeResult:
    """Test SharpeResult dataclass"""

    def test_sharpe_result_creation(self):
        result = SharpeResult(
            sharpe_ratio=Decimal("1.5"),
            annualized_return=Decimal("15"),
            risk_free_rate=Decimal("3"),
            volatility=Decimal("8"),
        )
        assert result.sharpe_ratio == Decimal("1.5")

    def test_sharpe_result_to_dict(self):
        result = SharpeResult(
            sharpe_ratio=Decimal("1.5"),
            annualized_return=Decimal("15"),
            risk_free_rate=Decimal("3"),
            volatility=Decimal("8"),
        )
        d = result.to_dict()
        assert d["夏普比率"] == "1.5000"


class TestVolatilityResult:
    """Test VolatilityResult dataclass"""

    def test_volatility_result_creation(self):
        result = VolatilityResult(
            daily_volatility=Decimal("1"),
            weekly_volatility=Decimal("2.24"),
            monthly_volatility=Decimal("4.58"),
            annualized_volatility=Decimal("15.87"),
        )
        assert result.daily_volatility == Decimal("1")

    def test_volatility_result_to_dict(self):
        result = VolatilityResult(
            daily_volatility=Decimal("1"),
            weekly_volatility=Decimal("2.24"),
            monthly_volatility=Decimal("4.58"),
            annualized_volatility=Decimal("15.87"),
        )
        d = result.to_dict()
        assert "日波动率" in d
        assert "年化波动率" in d


class TestAdvancedAnalytics:
    """Test AdvancedAnalytics class"""

    def setup_method(self):
        self.analytics = AdvancedAnalytics()

    def test_calculate_max_drawdown_empty(self):
        result = self.analytics.calculate_max_drawdown([])
        assert result.max_drawdown == Decimal("0")
        assert result.max_drawdown_percent == Decimal("0")

    def test_calculate_max_drawdown_single_value(self):
        result = self.analytics.calculate_max_drawdown([Decimal("100")])
        assert result.max_drawdown == Decimal("0")

    def test_calculate_max_drawdown_no_drawdown(self):
        values = [Decimal("100"), Decimal("110"), Decimal("120")]
        result = self.analytics.calculate_max_drawdown(values)
        assert result.max_drawdown == Decimal("0")

    def test_calculate_max_drawdown_simple(self):
        values = [Decimal("100"), Decimal("90"), Decimal("95")]
        result = self.analytics.calculate_max_drawdown(values)
        assert result.max_drawdown == Decimal("10")
        assert result.max_drawdown_percent == Decimal("10")

    def test_calculate_max_drawdown_with_dates(self):
        dates = [date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1)]
        values = [Decimal("100"), Decimal("80"), Decimal("90")]
        result = self.analytics.calculate_max_drawdown(values, dates)
        assert result.peak_date == date(2024, 1, 1)
        assert result.trough_date == date(2024, 2, 1)

    def test_calculate_max_drawdown_with_recovery(self):
        values = [Decimal("100"), Decimal("80"), Decimal("110")]
        dates = [date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1)]
        result = self.analytics.calculate_max_drawdown(values, dates)
        assert result.max_drawdown == Decimal("20")
        assert result.recovery_date == date(2024, 3, 1)

    def test_calculate_sharpe_ratio_empty(self):
        result = self.analytics.calculate_sharpe_ratio([])
        assert result.sharpe_ratio == Decimal("0")

    def test_calculate_sharpe_ratio_single_value(self):
        result = self.analytics.calculate_sharpe_ratio([Decimal("1")])
        assert result.sharpe_ratio == Decimal("0")

    def test_calculate_sharpe_ratio_positive(self):
        returns = [Decimal("1"), Decimal("2"), Decimal("1"), Decimal("2")]
        result = self.analytics.calculate_sharpe_ratio(returns)
        assert result.sharpe_ratio > Decimal("0")

    def test_calculate_sharpe_ratio_negative(self):
        returns = [Decimal("-1"), Decimal("-2"), Decimal("-1"), Decimal("-2")]
        result = self.analytics.calculate_sharpe_ratio(returns)
        assert result.sharpe_ratio < Decimal("0")

    def test_calculate_volatility_empty(self):
        result = self.analytics.calculate_volatility([])
        assert result.daily_volatility == Decimal("0")

    def test_calculate_volatility_single_value(self):
        result = self.analytics.calculate_volatility([Decimal("1")])
        assert result.daily_volatility == Decimal("0")

    def test_calculate_volatility_positive(self):
        returns = [Decimal("1"), Decimal("2"), Decimal("1"), Decimal("2")]
        result = self.analytics.calculate_volatility(returns)
        assert result.daily_volatility > Decimal("0")
        assert result.annualized_volatility > result.daily_volatility

    def test_calculate_returns_from_values_empty(self):
        result = self.analytics.calculate_returns_from_values([])
        assert result == []

    def test_calculate_returns_from_values_single(self):
        result = self.analytics.calculate_returns_from_values([Decimal("100")])
        assert result == []

    def test_calculate_returns_from_values_positive(self):
        values = [Decimal("100"), Decimal("110"), Decimal("121")]
        result = self.analytics.calculate_returns_from_values(values)
        assert len(result) == 2
        assert result[0] == Decimal("10")
        assert result[1] == Decimal("10")

    def test_calculate_returns_from_values_negative(self):
        values = [Decimal("100"), Decimal("90"), Decimal("81")]
        result = self.analytics.calculate_returns_from_values(values)
        assert len(result) == 2
        assert result[0] == Decimal("-10")
        assert result[1] == Decimal("-10")

    def test_analyze_portfolio_empty(self):
        portfolio = Portfolio()
        result = self.analytics.analyze_portfolio(portfolio)
        assert result.total_value == Decimal("0")
        assert result.return_rate == Decimal("0")

    def test_analyze_portfolio_with_products(self):
        portfolio = Portfolio()
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("11000"),
            initial_amount=Decimal("10000"),
            profit_amount=Decimal("1000"),
            start_date="2024-01-01",
        )
        portfolio.add_product(product)

        result = self.analytics.analyze_portfolio(portfolio)
        assert result.total_value == Decimal("11000")
        assert result.total_profit == Decimal("1000")

    def test_analyze_portfolio_with_history(self):
        portfolio = Portfolio()
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("11000"),
            initial_amount=Decimal("10000"),
            profit_amount=Decimal("1000"),
            start_date="2024-01-01",
        )
        portfolio.add_product(product)

        historical_values = [Decimal("10000"), Decimal("10500"), Decimal("11000")]
        historical_dates = [date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1)]

        result = self.analytics.analyze_portfolio(portfolio, historical_values, historical_dates)
        assert result.max_drawdown is not None
        assert result.sharpe_ratio is not None

    def test_calculate_correlation_empty(self):
        result = self.analytics.calculate_correlation([], [])
        assert result == Decimal("0")

    def test_calculate_correlation_different_lengths(self):
        result = self.analytics.calculate_correlation([Decimal("1")], [Decimal("1"), Decimal("2")])
        assert result == Decimal("0")

    def test_calculate_correlation_perfect_positive(self):
        returns1 = [Decimal("1"), Decimal("2"), Decimal("3")]
        returns2 = [Decimal("2"), Decimal("4"), Decimal("6")]
        result = self.analytics.calculate_correlation(returns1, returns2)
        assert result > Decimal("0.9")

    def test_calculate_correlation_perfect_negative(self):
        returns1 = [Decimal("1"), Decimal("2"), Decimal("3")]
        returns2 = [Decimal("3"), Decimal("2"), Decimal("1")]
        result = self.analytics.calculate_correlation(returns1, returns2)
        assert result < Decimal("-0.9")

    def test_calculate_beta_empty(self):
        result = self.analytics.calculate_beta([], [])
        assert result == Decimal("0")

    def test_calculate_beta_positive(self):
        portfolio_returns = [Decimal("1"), Decimal("2"), Decimal("1")]
        market_returns = [Decimal("0.5"), Decimal("1"), Decimal("0.5")]
        result = self.analytics.calculate_beta(portfolio_returns, market_returns)
        assert result > Decimal("0")

    def test_calculate_alpha(self):
        portfolio_return = Decimal("15")
        market_return = Decimal("10")
        beta = Decimal("1.2")
        result = self.analytics.calculate_alpha(portfolio_return, market_return, beta)
        assert result is not None


class TestGlobalInstance:
    """Test global analytics instance"""

    def test_global_instance_exists(self):
        assert advanced_analytics is not None
        assert isinstance(advanced_analytics, AdvancedAnalytics)

    def test_global_instance_works(self):
        result = advanced_analytics.calculate_max_drawdown([Decimal("100"), Decimal("90")])
        assert result.max_drawdown == Decimal("10")
