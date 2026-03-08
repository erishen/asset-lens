"""
Tests for backtester.py
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.data.backtester import Backtester, BacktestResult, BacktestTrade


class TestBacktestTrade:
    """BacktestTrade 测试"""

    def test_default_values(self):
        """测试默认值"""
        trade = BacktestTrade(
            date="2024-01-01",
            code="sh600519",
            name="贵州茅台",
            action="buy",
            price=1800.0,
            shares=100,
            amount=180000,
        )
        assert trade.date == "2024-01-01"
        assert trade.code == "sh600519"
        assert trade.name == "贵州茅台"
        assert trade.action == "buy"
        assert trade.price == 1800.0
        assert trade.shares == 100
        assert trade.amount == 180000
        assert trade.profit == 0
        assert trade.profit_rate == 0
        assert trade.reason == ""

    def test_custom_values(self):
        """测试自定义值"""
        trade = BacktestTrade(
            date="2024-01-01",
            code="sh600519",
            name="贵州茅台",
            action="sell",
            price=1900.0,
            shares=100,
            amount=190000,
            profit=10000,
            profit_rate=0.055,
            reason="止盈卖出",
        )
        assert trade.action == "sell"
        assert trade.profit == 10000
        assert trade.profit_rate == 0.055
        assert trade.reason == "止盈卖出"


class TestBacktestResult:
    """BacktestResult 测试"""

    def test_default_values(self):
        """测试默认值"""
        result = BacktestResult(
            strategy_name="test_strategy",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_capital=100000,
            final_capital=120000,
            total_return=0.2,
            annual_return=0.2,
            max_drawdown=0.1,
            win_rate=0.6,
            profit_factor=1.5,
            sharpe_ratio=1.2,
            total_trades=10,
            win_trades=6,
            lose_trades=4,
            avg_profit=5000,
            avg_loss=2000,
        )
        assert result.strategy_name == "test_strategy"
        assert result.initial_capital == 100000
        assert result.final_capital == 120000
        assert result.total_return == 0.2
        assert result.trades == []
        assert result.daily_values == []

    def test_with_trades(self):
        """测试带交易记录的结果"""
        trade = BacktestTrade(
            date="2024-01-01",
            code="sh600519",
            name="贵州茅台",
            action="buy",
            price=1800.0,
            shares=100,
            amount=180000,
        )
        result = BacktestResult(
            strategy_name="test_strategy",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_capital=100000,
            final_capital=120000,
            total_return=0.2,
            annual_return=0.2,
            max_drawdown=0.1,
            win_rate=0.6,
            profit_factor=1.5,
            sharpe_ratio=1.2,
            total_trades=10,
            win_trades=6,
            lose_trades=4,
            avg_profit=5000,
            avg_loss=2000,
            trades=[trade],
            daily_values=[{"date": "2024-01-01", "total_value": 100000}],
        )
        assert len(result.trades) == 1
        assert len(result.daily_values) == 1


class TestBacktester:
    """Backtester 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def backtester(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.data.backtester.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            backtester = Backtester()
            yield backtester

    def test_init(self, backtester):
        """测试初始化"""
        assert backtester.backtest_path.exists()

    def test_run_backtest_no_strategy(self, backtester):
        """测试运行回测 - 策略不存在"""
        with patch('asset_lens.data.strategy_engine.strategy_engine') as mock_engine:
            mock_engine.get_strategy.return_value = None

            with pytest.raises(ValueError):
                backtester.run_backtest("not_exist", {})

    def test_run_backtest_no_data(self, backtester):
        """测试运行回测 - 没有数据"""
        with patch('asset_lens.data.strategy_engine.strategy_engine') as mock_engine:
            mock_strategy = MagicMock()
            mock_strategy.name = "test_strategy"
            mock_engine.get_strategy.return_value = mock_strategy

            with pytest.raises(ValueError):
                backtester.run_backtest("test_strategy", {})

    def test_run_backtest_no_date_range(self, backtester):
        """测试运行回测 - 日期范围无数据"""
        with patch('asset_lens.data.strategy_engine.strategy_engine') as mock_engine:
            mock_strategy = MagicMock()
            mock_strategy.name = "test_strategy"
            mock_engine.get_strategy.return_value = mock_strategy

            historical_data = {
                "sh600519": [{"date": "2024-01-01", "close": 1800}]
            }

            with pytest.raises(ValueError):
                backtester.run_backtest("test_strategy", historical_data, start_date="2025-01-01")

    def test_save_backtest(self, backtester):
        """测试保存回测结果"""
        result = BacktestResult(
            strategy_name="test_strategy",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_capital=100000,
            final_capital=120000,
            total_return=0.2,
            annual_return=0.2,
            max_drawdown=0.1,
            win_rate=0.6,
            profit_factor=1.5,
            sharpe_ratio=1.2,
            total_trades=10,
            win_trades=6,
            lose_trades=4,
            avg_profit=5000,
            avg_loss=2000,
        )

        backtester._save_backtest(result)

        saved_files = list(backtester.backtest_path.glob("*.json"))
        assert len(saved_files) >= 1

    def test_save_backtest_with_trades(self, backtester):
        """测试保存带交易记录的回测结果"""
        trade = BacktestTrade(
            date="2024-01-01",
            code="sh600519",
            name="贵州茅台",
            action="buy",
            price=1800.0,
            shares=100,
            amount=180000,
        )
        result = BacktestResult(
            strategy_name="test_strategy",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_capital=100000,
            final_capital=120000,
            total_return=0.2,
            annual_return=0.2,
            max_drawdown=0.1,
            win_rate=0.6,
            profit_factor=1.5,
            sharpe_ratio=1.2,
            total_trades=10,
            win_trades=6,
            lose_trades=4,
            avg_profit=5000,
            avg_loss=2000,
            trades=[trade],
            daily_values=[{"date": "2024-01-01", "total_value": 100000}],
        )

        backtester._save_backtest(result)

        saved_files = list(backtester.backtest_path.glob("*.json"))
        assert len(saved_files) >= 1

    def test_compare_strategies(self, backtester):
        """测试比较多个策略"""
        with patch('asset_lens.data.strategy_engine.strategy_engine') as mock_engine:
            mock_strategy = MagicMock()
            mock_strategy.name = "test_strategy"
            mock_strategy.stop_loss = -0.1
            mock_strategy.take_profit = 0.2
            mock_strategy.holding_period_max = 30
            mock_strategy.max_positions = 5
            mock_strategy.position_size = 0.2
            mock_engine.get_strategy.return_value = mock_strategy
            mock_engine.evaluate_stock.return_value = {"match": False, "score": 0}

            historical_data = {
                "sh600519": [
                    {"date": "2024-01-01", "close": 1800, "name": "贵州茅台"},
                    {"date": "2024-01-02", "close": 1820, "name": "贵州茅台"},
                ]
            }

            results = backtester.compare_strategies(["test_strategy"], historical_data)
            assert "test_strategy" in results

    def test_compare_strategies_with_failure(self, backtester):
        """测试比较多个策略 - 部分失败"""
        with patch('asset_lens.data.strategy_engine.strategy_engine') as mock_engine:
            mock_engine.get_strategy.return_value = None

            historical_data = {
                "sh600519": [
                    {"date": "2024-01-01", "close": 1800, "name": "贵州茅台"},
                ]
            }

            results = backtester.compare_strategies(["not_exist"], historical_data)
            assert len(results) == 0

    def test_get_best_strategy(self, backtester):
        """测试获取最佳策略"""
        with patch('asset_lens.data.strategy_engine.strategy_engine') as mock_engine:
            mock_strategy = MagicMock()
            mock_strategy.name = "test_strategy"
            mock_strategy.stop_loss = -0.1
            mock_strategy.take_profit = 0.2
            mock_strategy.holding_period_max = 30
            mock_strategy.max_positions = 5
            mock_strategy.position_size = 0.2
            mock_engine.get_strategy.return_value = mock_strategy
            mock_engine.evaluate_stock.return_value = {"match": False, "score": 0}

            historical_data = {
                "sh600519": [
                    {"date": "2024-01-01", "close": 1800, "name": "贵州茅台"},
                    {"date": "2024-01-02", "close": 1820, "name": "贵州茅台"},
                ]
            }

            best_name, best_result = backtester.get_best_strategy(
                ["test_strategy"], historical_data
            )
            assert best_name == "test_strategy"

    def test_get_best_strategy_all_fail(self, backtester):
        """测试获取最佳策略 - 全部失败"""
        with patch('asset_lens.data.strategy_engine.strategy_engine') as mock_engine:
            mock_engine.get_strategy.return_value = None

            historical_data = {
                "sh600519": [
                    {"date": "2024-01-01", "close": 1800, "name": "贵州茅台"},
                ]
            }

            with pytest.raises(ValueError):
                backtester.get_best_strategy(["not_exist"], historical_data)

    def test_run_backtest_with_buy_signal(self, backtester):
        """测试运行回测 - 有买入信号"""
        with patch('asset_lens.data.strategy_engine.strategy_engine') as mock_engine:
            mock_strategy = MagicMock()
            mock_strategy.name = "test_strategy"
            mock_strategy.stop_loss = -0.1
            mock_strategy.take_profit = 0.2
            mock_strategy.holding_period_max = 30
            mock_strategy.max_positions = 5
            mock_strategy.position_size = 0.5
            mock_engine.get_strategy.return_value = mock_strategy
            mock_engine.evaluate_stock.return_value = {"match": True, "score": 70}

            historical_data = {
                "sh600519": [
                    {"date": "2024-01-01", "close": 100, "name": "贵州茅台"},
                    {"date": "2024-01-02", "close": 102, "name": "贵州茅台"},
                ]
            }

            result = backtester.run_backtest("test_strategy", historical_data)
            assert result.strategy_name == "test_strategy"
            assert len(result.trades) > 0

    def test_run_backtest_with_stop_loss(self, backtester):
        """测试运行回测 - 触发止损"""
        with patch('asset_lens.data.strategy_engine.strategy_engine') as mock_engine:
            mock_strategy = MagicMock()
            mock_strategy.name = "test_strategy"
            mock_strategy.stop_loss = -0.01
            mock_strategy.take_profit = 0.2
            mock_strategy.holding_period_max = 30
            mock_strategy.max_positions = 5
            mock_strategy.position_size = 0.2
            mock_engine.get_strategy.return_value = mock_strategy
            mock_engine.evaluate_stock.return_value = {"match": True, "score": 70}

            historical_data = {
                "sh600519": [
                    {"date": "2024-01-01", "close": 1800, "name": "贵州茅台"},
                    {"date": "2024-01-02", "close": 1700, "name": "贵州茅台"},
                ]
            }

            result = backtester.run_backtest("test_strategy", historical_data)
            assert result.strategy_name == "test_strategy"

    def test_run_backtest_with_take_profit(self, backtester):
        """测试运行回测 - 触发止盈"""
        with patch('asset_lens.data.strategy_engine.strategy_engine') as mock_engine:
            mock_strategy = MagicMock()
            mock_strategy.name = "test_strategy"
            mock_strategy.stop_loss = -0.1
            mock_strategy.take_profit = 0.01
            mock_strategy.holding_period_max = 30
            mock_strategy.max_positions = 5
            mock_strategy.position_size = 0.2
            mock_engine.get_strategy.return_value = mock_strategy
            mock_engine.evaluate_stock.return_value = {"match": True, "score": 70}

            historical_data = {
                "sh600519": [
                    {"date": "2024-01-01", "close": 1800, "name": "贵州茅台"},
                    {"date": "2024-01-02", "close": 1900, "name": "贵州茅台"},
                ]
            }

            result = backtester.run_backtest("test_strategy", historical_data)
            assert result.strategy_name == "test_strategy"

    def test_run_backtest_with_holding_period(self, backtester):
        """测试运行回测 - 触发持有期限制"""
        with patch('asset_lens.data.strategy_engine.strategy_engine') as mock_engine:
            mock_strategy = MagicMock()
            mock_strategy.name = "test_strategy"
            mock_strategy.stop_loss = -0.1
            mock_strategy.take_profit = 0.2
            mock_strategy.holding_period_max = 1
            mock_strategy.max_positions = 5
            mock_strategy.position_size = 0.2
            mock_engine.get_strategy.return_value = mock_strategy
            mock_engine.evaluate_stock.return_value = {"match": True, "score": 70}

            historical_data = {
                "sh600519": [
                    {"date": "2024-01-01", "close": 1800, "name": "贵州茅台"},
                    {"date": "2024-01-02", "close": 1800, "name": "贵州茅台"},
                ]
            }

            result = backtester.run_backtest("test_strategy", historical_data)
            assert result.strategy_name == "test_strategy"
