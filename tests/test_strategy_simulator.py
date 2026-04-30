"""
Tests for Strategy Simulator - 策略模拟器测试

覆盖边界场景:
- 空池模拟
- 价格缺失
- 最短持仓
- 止损类型
- 基准收益计算
"""

from datetime import datetime, timedelta

import pytest

from asset_lens.trading.strategy_simulator import (
    RebalanceFrequency,
    SimulatedPosition,
    SimulationConfig,
    StopLossType,
    StrategySimulator,
)


class TestStrategySimulator:
    """策略模拟器测试"""

    def test_empty_pool_simulation(self):
        """测试空池模拟"""
        config = SimulationConfig(
            initial_capital=1000000,
            max_positions=10,
        )
        simulator = StrategySimulator(config)

        price_history = {
            "sh600519": [
                {"date": "2024-01-01", "price": 100.0},
                {"date": "2024-01-02", "price": 101.0},
            ]
        }

        result = simulator.run_simulation(
            stock_pool_data=[],
            price_history=price_history,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert result is not None
        assert result.total_return == 0.0
        assert result.total_trades == 0

    def test_missing_price_data(self):
        """测试价格缺失场景"""
        config = SimulationConfig(
            initial_capital=1000000,
            max_positions=10,
        )
        simulator = StrategySimulator(config)

        stock_pool_data = [
            {"code": "sh600519", "name": "贵州茅台", "score": 80},
        ]

        price_history = {
            "sh600519": [],  # 空价格历史
        }

        result = simulator.run_simulation(
            stock_pool_data=stock_pool_data,
            price_history=price_history,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert result is not None

    def test_single_stock_simulation(self):
        """测试单只股票模拟"""
        config = SimulationConfig(
            initial_capital=1000000,
            max_positions=10,
            rebalance_frequency=RebalanceFrequency.WEEKLY,
        )
        simulator = StrategySimulator(config)

        stock_pool_data = [
            {"code": "sh600519", "name": "贵州茅台", "score": 80},
        ]

        price_history = {
            "sh600519": [
                {"date": "2024-01-01", "price": 100.0},
                {"date": "2024-01-02", "price": 102.0},
                {"date": "2024-01-03", "price": 105.0},
            ]
        }

        result = simulator.run_simulation(
            stock_pool_data=stock_pool_data,
            price_history=price_history,
            start_date="2024-01-01",
            end_date="2024-01-03",
        )

        assert result is not None
        assert result.total_return >= 0

    def test_min_holding_days(self):
        """测试最小持有天数"""
        config = SimulationConfig(
            initial_capital=1000000,
            max_positions=10,
            min_holding_days=5,
            rebalance_frequency=RebalanceFrequency.DAILY,
        )
        simulator = StrategySimulator(config)

        stock_pool_data = [
            {"code": "sh600519", "name": "贵州茅台", "score": 80},
        ]

        dates = [(datetime(2024, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10)]
        price_history = {"sh600519": [{"date": d, "price": 100.0 + i} for i, d in enumerate(dates)]}

        result = simulator.run_simulation(
            stock_pool_data=stock_pool_data,
            price_history=price_history,
            start_date="2024-01-01",
            end_date="2024-01-10",
        )

        assert result is not None

    def test_max_holding_days(self):
        """测试最大持有天数"""
        config = SimulationConfig(
            initial_capital=1000000,
            max_positions=10,
            max_holding_days=5,
            rebalance_frequency=RebalanceFrequency.DAILY,
        )
        simulator = StrategySimulator(config)

        stock_pool_data = [
            {"code": "sh600519", "name": "贵州茅台", "score": 80},
        ]

        dates = [(datetime(2024, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10)]
        price_history = {"sh600519": [{"date": d, "price": 100.0} for i, d in enumerate(dates)]}

        result = simulator.run_simulation(
            stock_pool_data=stock_pool_data,
            price_history=price_history,
            start_date="2024-01-01",
            end_date="2024-01-10",
        )

        assert result is not None

    def test_benchmark_return_calculation(self):
        """测试基准收益计算"""
        config = SimulationConfig(
            initial_capital=1000000,
            max_positions=10,
        )
        simulator = StrategySimulator(config)

        stock_pool_data = [
            {"code": "sh600519", "name": "贵州茅台", "score": 80},
        ]

        price_history = {
            "sh600519": [
                {"date": "2024-01-01", "price": 100.0},
                {"date": "2024-01-02", "price": 110.0},
            ]
        }

        benchmark_prices = {
            "2024-01-01": 3000.0,
            "2024-01-02": 3150.0,  # 5% 涨幅
        }

        result = simulator.run_simulation(
            stock_pool_data=stock_pool_data,
            price_history=price_history,
            start_date="2024-01-01",
            end_date="2024-01-02",
            benchmark_prices=benchmark_prices,
        )

        assert result is not None
        assert result.benchmark_return == pytest.approx(5.0, rel=0.01)

    def test_excess_return_calculation(self):
        """测试超额收益计算"""
        config = SimulationConfig(
            initial_capital=1000000,
            max_positions=10,
        )
        simulator = StrategySimulator(config)

        stock_pool_data = [
            {"code": "sh600519", "name": "贵州茅台", "score": 80},
        ]

        price_history = {
            "sh600519": [
                {"date": "2024-01-01", "price": 100.0},
                {"date": "2024-01-02", "price": 110.0},  # 10% 涨幅
            ]
        }

        benchmark_prices = {
            "2024-01-01": 3000.0,
            "2024-01-02": 3150.0,  # 5% 涨幅
        }

        result = simulator.run_simulation(
            stock_pool_data=stock_pool_data,
            price_history=price_history,
            start_date="2024-01-01",
            end_date="2024-01-02",
            benchmark_prices=benchmark_prices,
        )

        assert result is not None
        assert result.benchmark_return == pytest.approx(5.0, rel=0.01)
        # 超额收益 = 策略收益 - 基准收益


class TestStopLoss:
    """止损测试"""

    def test_fixed_stop_loss(self):
        """测试固定止损"""
        config = SimulationConfig(
            initial_capital=1000000,
            stop_loss_pct=0.08,
            stop_loss_type=StopLossType.FIXED,
        )
        simulator = StrategySimulator(config)

        stock_pool_data = [
            {"code": "sh600519", "name": "贵州茅台", "score": 80},
        ]

        price_history = {
            "sh600519": [
                {"date": "2024-01-01", "price": 100.0},
                {"date": "2024-01-02", "price": 91.0},  # 跌破 8% 止损线
            ]
        }

        result = simulator.run_simulation(
            stock_pool_data=stock_pool_data,
            price_history=price_history,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert result is not None

    def test_trailing_stop_loss(self):
        """测试追踪止损"""
        config = SimulationConfig(
            initial_capital=1000000,
            stop_loss_pct=0.08,
            stop_loss_type=StopLossType.TRAILING,
        )
        simulator = StrategySimulator(config)

        stock_pool_data = [
            {"code": "sh600519", "name": "贵州茅台", "score": 80},
        ]

        price_history = {
            "sh600519": [
                {"date": "2024-01-01", "price": 100.0},
                {"date": "2024-01-02", "price": 110.0},  # 最高价
                {"date": "2024-01-03", "price": 100.0},  # 回撤 9%，跌破追踪止损
            ]
        }

        result = simulator.run_simulation(
            stock_pool_data=stock_pool_data,
            price_history=price_history,
            start_date="2024-01-01",
            end_date="2024-01-03",
        )

        assert result is not None

    def test_atr_stop_loss(self):
        """测试 ATR 止损"""
        config = SimulationConfig(
            initial_capital=1000000,
            stop_loss_pct=0.08,
            stop_loss_type=StopLossType.ATR_BASED,
        )
        simulator = StrategySimulator(config)

        stock_pool_data = [
            {"code": "sh600519", "name": "贵州茅台", "score": 80},
        ]

        price_history = {
            "sh600519": [
                {"date": "2024-01-01", "price": 100.0},
                {"date": "2024-01-02", "price": 95.0},
            ]
        }

        result = simulator.run_simulation(
            stock_pool_data=stock_pool_data,
            price_history=price_history,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert result is not None


class TestSimulationConfig:
    """模拟配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = SimulationConfig()

        assert config.initial_capital == 1000000.0
        assert config.max_positions == 10
        assert config.stop_loss_pct == 0.08
        assert config.take_profit_pct == 0.20
        assert config.stop_loss_type == StopLossType.FIXED

    def test_custom_config(self):
        """测试自定义配置"""
        config = SimulationConfig(
            initial_capital=500000,
            max_positions=5,
            stop_loss_pct=0.10,
            take_profit_pct=0.30,
            stop_loss_type=StopLossType.TRAILING,
            min_holding_days=3,
            max_holding_days=30,
        )

        assert config.initial_capital == 500000
        assert config.max_positions == 5
        assert config.stop_loss_pct == 0.10
        assert config.take_profit_pct == 0.30
        assert config.stop_loss_type == StopLossType.TRAILING
        assert config.min_holding_days == 3
        assert config.max_holding_days == 30


class TestSimulatedPosition:
    """模拟持仓测试"""

    def test_position_creation(self):
        """测试持仓创建"""
        position = SimulatedPosition(
            code="sh600519",
            name="贵州茅台",
            entry_date="2024-01-01",
            entry_price=100.0,
            shares=1000,
            weight=0.1,
        )

        assert position.code == "sh600519"
        assert position.entry_price == 100.0
        assert position.shares == 1000

    def test_position_update_price(self):
        """测试持仓价格更新"""
        position = SimulatedPosition(
            code="sh600519",
            name="贵州茅台",
            entry_date="2024-01-01",
            entry_price=100.0,
            shares=1000,
            weight=0.1,
            stop_loss_pct=0.08,
        )

        position.update_price(110.0)

        assert position.current_price == 110.0
        assert position.highest_price == 110.0
        assert position.profit == 10000.0  # (110 - 100) * 1000
        assert position.profit_rate == pytest.approx(0.1, rel=0.01)

    def test_position_stop_loss_check(self):
        """测试持仓止损检查"""
        position = SimulatedPosition(
            code="sh600519",
            name="贵州茅台",
            entry_date="2024-01-01",
            entry_price=100.0,
            shares=1000,
            weight=0.1,
            stop_loss_price=92.0,  # 8% 止损
        )

        position.update_price(91.0)

        assert position.should_stop_loss() is True

    def test_position_take_profit_check(self):
        """测试持仓止盈检查"""
        position = SimulatedPosition(
            code="sh600519",
            name="贵州茅台",
            entry_date="2024-01-01",
            entry_price=100.0,
            shares=1000,
            weight=0.1,
            take_profit_price=120.0,  # 20% 止盈
        )

        position.update_price(121.0)

        assert position.should_take_profit() is True
