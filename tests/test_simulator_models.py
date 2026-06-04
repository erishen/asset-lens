import pytest

from asset_lens.trading.simulator_models import (
    RebalanceFrequency,
    SimulatedPosition,
    SimulatedTrade,
    SimulationConfig,
    StopLossType,
)


class TestRebalanceFrequency:
    def test_values(self):
        assert RebalanceFrequency.DAILY.value == "daily"
        assert RebalanceFrequency.WEEKLY.value == "weekly"
        assert RebalanceFrequency.MONTHLY.value == "monthly"
        assert RebalanceFrequency.QUARTERLY.value == "quarterly"


class TestStopLossType:
    def test_values(self):
        assert StopLossType.FIXED.value == "fixed"
        assert StopLossType.TRAILING.value == "trailing"
        assert StopLossType.ATR_BASED.value == "atr_based"


class TestSimulationConfig:
    def test_default_values(self):
        cfg = SimulationConfig()
        assert cfg.initial_capital == 1000000.0
        assert cfg.max_positions == 10
        assert cfg.max_position_weight == 0.15
        assert cfg.min_position_weight == 0.05
        assert cfg.rebalance_frequency == RebalanceFrequency.WEEKLY
        assert cfg.stop_loss_pct == 0.08
        assert cfg.take_profit_pct == 0.20
        assert cfg.stop_loss_type == StopLossType.FIXED
        assert cfg.commission_rate == 0.0003
        assert cfg.slippage_rate == 0.001

    def test_custom_values(self):
        cfg = SimulationConfig(
            initial_capital=500000.0,
            max_positions=5,
            stop_loss_pct=0.05,
            stop_loss_type=StopLossType.TRAILING,
        )
        assert cfg.initial_capital == 500000.0
        assert cfg.max_positions == 5
        assert cfg.stop_loss_pct == 0.05
        assert cfg.stop_loss_type == StopLossType.TRAILING


class TestSimulatedPosition:
    def test_creation(self):
        pos = SimulatedPosition(
            code="600519",
            name="贵州茅台",
            entry_date="2025-01-01",
            entry_price=1800.0,
            shares=100,
            weight=0.15,
        )
        assert pos.code == "600519"
        assert pos.entry_price == 1800.0
        assert pos.current_price == 0.0
        assert pos.highest_price == 0.0

    def test_update_price(self):
        pos = SimulatedPosition(
            code="600519",
            name="贵州茅台",
            entry_date="2025-01-01",
            entry_price=1800.0,
            shares=100,
            weight=0.15,
        )
        pos.update_price(1900.0)
        assert pos.current_price == 1900.0
        assert pos.current_value == 190000.0
        assert pos.profit == 10000.0
        assert pos.profit_rate == pytest.approx(0.0556, rel=0.01)
        assert pos.highest_price == 1900.0

    def test_update_price_tracks_highest(self):
        pos = SimulatedPosition(
            code="600519",
            name="贵州茅台",
            entry_date="2025-01-01",
            entry_price=1800.0,
            shares=100,
            weight=0.15,
        )
        pos.update_price(1900.0)
        pos.update_price(1850.0)
        assert pos.highest_price == 1900.0
        assert pos.current_price == 1850.0

    def test_stop_loss_fixed(self):
        pos = SimulatedPosition(
            code="600519",
            name="贵州茅台",
            entry_date="2025-01-01",
            entry_price=1800.0,
            shares=100,
            weight=0.15,
            stop_loss_type=StopLossType.FIXED,
            stop_loss_pct=0.08,
        )
        pos.update_price(1800.0)
        assert pos.stop_loss_price == pytest.approx(1800.0 * 0.92)

    def test_stop_loss_trailing(self):
        pos = SimulatedPosition(
            code="600519",
            name="贵州茅台",
            entry_date="2025-01-01",
            entry_price=1800.0,
            shares=100,
            weight=0.15,
            stop_loss_type=StopLossType.TRAILING,
            stop_loss_pct=0.08,
        )
        pos.highest_price = 1800.0
        pos.update_price(1850.0)
        assert pos.highest_price == 1850.0
        pos.update_price(1900.0)
        assert pos.highest_price == 1900.0
        pos.stop_loss_price = pos.highest_price * (1 - pos.stop_loss_pct)
        assert pos.stop_loss_price == pytest.approx(1900.0 * 0.92)

    def test_stop_loss_atr_based(self):
        pos = SimulatedPosition(
            code="600519",
            name="贵州茅台",
            entry_date="2025-01-01",
            entry_price=1800.0,
            shares=100,
            weight=0.15,
            stop_loss_type=StopLossType.ATR_BASED,
            stop_loss_pct=0.08,
            _atr=50.0,
            _atr_multiplier=2.0,
        )
        pos.update_price(1850.0)
        assert pos.stop_loss_price == pytest.approx(1850.0 - 50.0 * 2.0)

    def test_stop_loss_atr_no_atr(self):
        pos = SimulatedPosition(
            code="600519",
            name="贵州茅台",
            entry_date="2025-01-01",
            entry_price=1800.0,
            shares=100,
            weight=0.15,
            stop_loss_type=StopLossType.ATR_BASED,
            stop_loss_pct=0.08,
            _atr=None,
        )
        pos.update_price(1800.0)
        assert pos.stop_loss_price == pytest.approx(1800.0 * 0.92)

    def test_should_stop_loss(self):
        pos = SimulatedPosition(
            code="600519",
            name="贵州茅台",
            entry_date="2025-01-01",
            entry_price=1800.0,
            shares=100,
            weight=0.15,
            stop_loss_type=StopLossType.FIXED,
            stop_loss_pct=0.08,
        )
        pos.update_price(1600.0)
        assert pos.should_stop_loss() is True

    def test_should_not_stop_loss(self):
        pos = SimulatedPosition(
            code="600519",
            name="贵州茅台",
            entry_date="2025-01-01",
            entry_price=1800.0,
            shares=100,
            weight=0.15,
            stop_loss_type=StopLossType.FIXED,
            stop_loss_pct=0.08,
        )
        pos.update_price(1700.0)
        assert pos.should_stop_loss() is False

    def test_should_stop_loss_zero_price(self):
        pos = SimulatedPosition(
            code="600519",
            name="贵州茅台",
            entry_date="2025-01-01",
            entry_price=1800.0,
            shares=100,
            weight=0.15,
        )
        assert pos.should_stop_loss() is False

    def test_should_take_profit(self):
        pos = SimulatedPosition(
            code="600519",
            name="贵州茅台",
            entry_date="2025-01-01",
            entry_price=1800.0,
            shares=100,
            weight=0.15,
            take_profit_price=2000.0,
        )
        pos.update_price(2100.0)
        assert pos.should_take_profit() is True

    def test_should_not_take_profit(self):
        pos = SimulatedPosition(
            code="600519",
            name="贵州茅台",
            entry_date="2025-01-01",
            entry_price=1800.0,
            shares=100,
            weight=0.15,
            take_profit_price=2000.0,
        )
        pos.update_price(1900.0)
        assert pos.should_take_profit() is False

    def test_should_take_profit_zero_price(self):
        pos = SimulatedPosition(
            code="600519",
            name="贵州茅台",
            entry_date="2025-01-01",
            entry_price=1800.0,
            shares=100,
            weight=0.15,
            take_profit_price=0.0,
        )
        assert pos.should_take_profit() is False


class TestSimulatedTrade:
    def test_creation(self):
        trade = SimulatedTrade(
            date="2025-01-01",
            code="600519",
            name="贵州茅台",
            action="buy",
            price=1800.0,
            shares=100,
            amount=180000.0,
            commission=54.0,
            slippage=180.0,
            reason="策略信号",
        )
        assert trade.code == "600519"
        assert trade.profit == 0.0
        assert trade.profit_rate == 0.0
