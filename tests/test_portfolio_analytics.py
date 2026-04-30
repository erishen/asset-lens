"""
Tests for portfolio analytics module.
"""

from asset_lens.core.portfolio_analytics import PortfolioAnalytics, PortfolioMetrics, RiskMetrics, portfolio_analytics


class TestPortfolioMetrics:
    """Test PortfolioMetrics dataclass"""

    def test_creation(self):
        """Test creating PortfolioMetrics"""
        metrics = PortfolioMetrics(
            total_return=10.0,
            annualized_return=5.0,
            volatility=15.0,
            sharpe_ratio=0.5,
            max_drawdown=5.0,
            win_rate=60.0,
            profit_loss_ratio=1.5,
            calmar_ratio=1.0,
            sortino_ratio=0.7,
        )

        assert metrics.total_return == 10.0
        assert metrics.annualized_return == 5.0
        assert metrics.volatility == 15.0


class TestRiskMetrics:
    """Test RiskMetrics dataclass"""

    def test_creation(self):
        """Test creating RiskMetrics"""
        metrics = RiskMetrics(
            value_at_risk_95=2.0,
            value_at_risk_99=3.0,
            expected_shortfall=2.5,
            beta=1.2,
            tracking_error=5.0,
            information_ratio=0.3,
        )

        assert metrics.value_at_risk_95 == 2.0
        assert metrics.beta == 1.2


class TestPortfolioAnalytics:
    """Test PortfolioAnalytics class"""

    def test_init(self):
        """Test initialization"""
        analytics = PortfolioAnalytics()
        assert analytics.risk_free_rate == 0.02

        analytics2 = PortfolioAnalytics(risk_free_rate=0.03)
        assert analytics2.risk_free_rate == 0.03

    def test_calculate_metrics_empty(self):
        """Test calculating metrics with empty returns"""
        analytics = PortfolioAnalytics()
        metrics = analytics.calculate_metrics([])

        assert metrics.total_return == 0.0
        assert metrics.annualized_return == 0.0

    def test_calculate_metrics_positive(self):
        """Test calculating metrics with positive returns"""
        analytics = PortfolioAnalytics()
        returns = [0.01, 0.02, 0.015, 0.005, 0.01]
        metrics = analytics.calculate_metrics(returns)

        assert metrics.total_return > 0
        assert metrics.win_rate == 100.0

    def test_calculate_metrics_mixed(self):
        """Test calculating metrics with mixed returns"""
        analytics = PortfolioAnalytics()
        returns = [0.01, -0.02, 0.015, -0.005, 0.01]
        metrics = analytics.calculate_metrics(returns)

        assert metrics.win_rate == 60.0
        assert metrics.profit_loss_ratio > 0

    def test_calculate_total_return(self):
        """Test calculating total return"""
        analytics = PortfolioAnalytics()
        returns = [0.1, 0.1, 0.1]

        total = analytics._calculate_total_return(returns)
        assert abs(total - 33.1) < 0.1

    def test_calculate_volatility(self):
        """Test calculating volatility"""
        analytics = PortfolioAnalytics()
        returns = [0.01, 0.02, 0.01, 0.02, 0.01]

        vol = analytics._calculate_volatility(returns)
        assert vol > 0

    def test_calculate_max_drawdown(self):
        """Test calculating max drawdown"""
        analytics = PortfolioAnalytics()
        returns = [0.1, -0.05, -0.05, 0.1]

        dd = analytics._calculate_max_drawdown(returns)
        assert dd > 0

    def test_calculate_win_rate(self):
        """Test calculating win rate"""
        analytics = PortfolioAnalytics()
        returns = [0.01, 0.02, -0.01, 0.01, -0.02]

        win_rate = analytics._calculate_win_rate(returns)
        assert win_rate == 60.0

    def test_calculate_profit_loss_ratio(self):
        """Test calculating profit loss ratio"""
        analytics = PortfolioAnalytics()
        returns = [0.02, 0.04, -0.01, -0.02]

        ratio = analytics._calculate_profit_loss_ratio(returns)
        assert ratio == 2.0

    def test_calculate_risk_metrics_empty(self):
        """Test calculating risk metrics with empty returns"""
        analytics = PortfolioAnalytics()
        metrics = analytics.calculate_risk_metrics([])

        assert metrics.value_at_risk_95 == 0.0
        assert metrics.beta == 1.0

    def test_calculate_var(self):
        """Test calculating VaR"""
        analytics = PortfolioAnalytics()
        returns = [-0.05, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03, 0.04, 0.05]

        var_95 = analytics._calculate_var(returns, 0.95)
        assert var_95 > 0

    def test_calculate_beta(self):
        """Test calculating beta"""
        analytics = PortfolioAnalytics()
        returns = [0.01, 0.02, -0.01, 0.02]
        benchmark = [0.01, 0.015, -0.005, 0.015]

        beta = analytics._calculate_beta(returns, benchmark)
        assert beta > 0

    def test_generate_report(self):
        """Test generating report"""
        analytics = PortfolioAnalytics()
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]

        report = analytics.generate_report(returns)

        assert "performance" in report
        assert "risk" in report
        assert "evaluation" in report

    def test_generate_evaluation(self):
        """Test generating evaluation"""
        analytics = PortfolioAnalytics()

        metrics = PortfolioMetrics(
            total_return=15.0,
            annualized_return=12.0,
            volatility=8.0,
            sharpe_ratio=1.5,
            max_drawdown=5.0,
            win_rate=65.0,
            profit_loss_ratio=2.0,
            calmar_ratio=2.4,
            sortino_ratio=2.0,
        )

        risk_metrics = RiskMetrics(
            value_at_risk_95=2.0,
            value_at_risk_99=3.0,
            expected_shortfall=2.5,
            beta=1.0,
            tracking_error=0.0,
            information_ratio=0.0,
        )

        evaluation = analytics._generate_evaluation(metrics, risk_metrics)
        assert "收益率优秀" in evaluation
        assert "波动率低" in evaluation


class TestGlobalInstance:
    """Test global instance"""

    def test_global_instance(self):
        """Test global instance exists"""
        assert portfolio_analytics is not None
        assert isinstance(portfolio_analytics, PortfolioAnalytics)
