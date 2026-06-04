from unittest.mock import MagicMock

import pytest

from asset_lens.monitoring.risk_alert_checks import AlertLevel, RiskAlertChecksMixin


class FakeRiskMonitor(RiskAlertChecksMixin):
    def __init__(self):
        self.config = MagicMock()
        self.config.max_drawdown_threshold = 0.15
        self.config.volatility_threshold = 0.25
        self.config.concentration_threshold = 0.3
        self.config.stop_loss_threshold = -0.08
        self.config.take_profit_threshold = 0.15
        self.config.position_limit = 0.8
        self.config.price_change_threshold = 0.05
        self._alerts = []

    def _create_alert(self, alert_type, level, title, message, data):
        alert = MagicMock()
        alert.alert_type = alert_type
        alert.level = level
        alert.title = title
        alert.message = message
        alert.data = data
        self._alerts.append(alert)
        return alert


@pytest.fixture
def monitor():
    return FakeRiskMonitor()


class TestAlertLevel:
    def test_values(self):
        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.CRITICAL.value == "critical"


class TestCheckMaxDrawdown:
    def test_trigger_warning(self, monitor):
        result = monitor.check_max_drawdown(-0.16, "default")
        assert result is not None
        assert result.level == AlertLevel.WARNING

    def test_trigger_critical(self, monitor):
        result = monitor.check_max_drawdown(-0.23, "default")
        assert result is not None
        assert result.level == AlertLevel.CRITICAL

    def test_no_alert(self, monitor):
        result = monitor.check_max_drawdown(-0.10, "default")
        assert result is None


class TestCheckVolatility:
    def test_trigger(self, monitor):
        result = monitor.check_volatility(0.30, "default")
        assert result is not None

    def test_no_alert(self, monitor):
        result = monitor.check_volatility(0.20, "default")
        assert result is None


class TestCheckConcentration:
    def test_trigger(self, monitor):
        holdings = {"600519": 40000, "000858": 10000}
        result = monitor.check_concentration(holdings)
        assert result is not None

    def test_no_alert(self, monitor):
        holdings = {"600519": 10000, "000858": 10000, "stock_c": 10000, "stock_d": 10000}
        result = monitor.check_concentration(holdings)
        assert result is None

    def test_empty_holdings(self, monitor):
        result = monitor.check_concentration({})
        assert result is None

    def test_zero_total(self, monitor):
        result = monitor.check_concentration({"600519": 0})
        assert result is None


class TestCheckStopLoss:
    def test_trigger(self, monitor):
        result = monitor.check_stop_loss(15.0, 20.0, "贵州茅台", "600519")
        assert result is not None
        assert result.level == AlertLevel.CRITICAL

    def test_no_alert(self, monitor):
        result = monitor.check_stop_loss(19.0, 20.0, "贵州茅台", "600519")
        assert result is None

    def test_zero_cost(self, monitor):
        result = monitor.check_stop_loss(15.0, 0, "贵州茅台", "600519")
        assert result is None


class TestCheckTakeProfit:
    def test_trigger(self, monitor):
        result = monitor.check_take_profit(25.0, 20.0, "贵州茅台", "600519")
        assert result is not None
        assert result.level == AlertLevel.INFO

    def test_no_alert(self, monitor):
        result = monitor.check_take_profit(22.0, 20.0, "贵州茅台", "600519")
        assert result is None

    def test_zero_cost(self, monitor):
        result = monitor.check_take_profit(25.0, 0, "贵州茅台", "600519")
        assert result is None


class TestCheckPositionLimit:
    def test_trigger(self, monitor):
        result = monitor.check_position_limit(0.85)
        assert result is not None

    def test_no_alert(self, monitor):
        result = monitor.check_position_limit(0.70)
        assert result is None


class TestCheckPriceChange:
    def test_trigger_warning(self, monitor):
        result = monitor.check_price_change("贵州茅台", "600519", 0.06)
        assert result is not None
        assert result.level == AlertLevel.WARNING

    def test_trigger_critical(self, monitor):
        result = monitor.check_price_change("贵州茅台", "600519", 0.12)
        assert result is not None
        assert result.level == AlertLevel.CRITICAL

    def test_no_alert(self, monitor):
        result = monitor.check_price_change("贵州茅台", "600519", 0.03)
        assert result is None


class TestCheckMarketRegime:
    def test_crash(self, monitor):
        result = monitor.check_market_regime("crash", "市场暴跌")
        assert result is not None
        assert result.level == AlertLevel.CRITICAL

    def test_extreme_volatility(self, monitor):
        result = monitor.check_market_regime("extreme_volatility", "极端波动")
        assert result is not None
        assert result.level == AlertLevel.CRITICAL

    def test_bear(self, monitor):
        result = monitor.check_market_regime("bear", "熊市")
        assert result is not None
        assert result.level == AlertLevel.WARNING

    def test_high_volatility(self, monitor):
        result = monitor.check_market_regime("high_volatility", "高波动")
        assert result is not None
        assert result.level == AlertLevel.WARNING

    def test_normal(self, monitor):
        result = monitor.check_market_regime("normal", "正常")
        assert result is None

    def test_bull(self, monitor):
        result = monitor.check_market_regime("bull", "牛市")
        assert result is None


class TestRunAllChecks:
    def test_with_portfolio_data(self, monitor):
        portfolio_data = {
            "name": "test",
            "max_drawdown": -0.20,
            "volatility": 0.30,
            "holdings": {"600519": 40000, "000858": 10000},
            "total_position": 0.85,
        }
        alerts = monitor.run_all_checks(portfolio_data)
        assert len(alerts) >= 3

    def test_with_market_data(self, monitor):
        portfolio_data = {"name": "test"}
        market_data = {
            "regime": "crash",
            "description": "暴跌",
            "stocks": [
                {"name": "贵州茅台", "code": "600519", "change_percent": 0.08},
            ],
        }
        alerts = monitor.run_all_checks(portfolio_data, market_data)
        assert len(alerts) >= 2

    def test_no_alerts(self, monitor):
        portfolio_data = {
            "name": "test",
            "max_drawdown": -0.05,
            "volatility": 0.10,
            "holdings": {"600519": 10000, "000858": 10000, "stock_c": 10000, "stock_d": 10000},
            "total_position": 0.50,
        }
        alerts = monitor.run_all_checks(portfolio_data)
        assert len(alerts) == 0

    def test_empty_data(self, monitor):
        alerts = monitor.run_all_checks({})
        assert len(alerts) == 0
