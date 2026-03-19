"""
Tests for investment_system.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.data.investment_system import InvestmentSystem


class TestInvestmentSystem:
    """InvestmentSystem 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def system(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.data.investment_system.config') as mock_config, \
             patch('asset_lens.data.investment_system.StockPool') as mock_pool, \
             patch('asset_lens.data.investment_system.Backtester') as mock_backtester:
            mock_config.cache_path = temp_cache_path
            mock_pool_instance = MagicMock()
            mock_pool_instance.positions = {}
            mock_pool.return_value = mock_pool_instance
            mock_backtester.return_value = MagicMock()

            system = InvestmentSystem("test_system")
            yield system

    def test_init(self, system):
        """测试初始化"""
        assert system.system_name == "test_system"
        assert system.stock_pool is not None
        assert system.backtester is not None

    def test_load_config_no_file(self, system):
        """测试加载配置 - 文件不存在"""
        system._load_config()
        assert system.system_config == {}
        assert system.current_strategy is None

    def test_load_config_with_file(self, system):
        """测试加载配置 - 有文件"""
        config_data = {
            "current_strategy": "momentum",
            "update_time": "2024-01-01 12:00:00",
        }
        with open(system.config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        system._load_config()
        assert system.current_strategy == "momentum"

    def test_set_strategy_success(self, system):
        """测试设置策略 - 成功"""
        with patch('asset_lens.data.investment_system.strategy_engine') as mock_engine:
            mock_engine.strategies = {"momentum": MagicMock(), "value": MagicMock()}

            result = system.set_strategy("momentum")

            assert result is True
            assert system.current_strategy == "momentum"

    def test_set_strategy_not_found(self, system):
        """测试设置策略 - 不存在"""
        with patch('asset_lens.data.investment_system.strategy_engine') as mock_engine:
            mock_engine.strategies = {"momentum": MagicMock()}

            result = system.set_strategy("not_exist")

            assert result is False

    def test_screen_and_add_to_pool(self, system):
        """测试筛选股票并添加到股票池"""
        with patch('asset_lens.data.investment_system.strategy_engine') as mock_engine:
            system.current_strategy = "momentum"
            mock_engine.screen_stocks.return_value = [
                {"code": "sh600519", "name": "贵州茅台", "current_price": 1800, "strategy_score": 85},
            ]

            stocks = [{"code": "sh600519", "name": "贵州茅台", "current_price": 1800}]
            system.stock_pool.add_stock.return_value = True

            result = system.screen_and_add_to_pool(stocks)

            assert result >= 0

    def test_simulate_buy(self, system):
        """测试模拟买入"""
        system.stock_pool.positions = {"sh600519": MagicMock(current_price=1800)}
        system.stock_pool.buy_stock.return_value = (True, "买入成功")

        result = system.simulate_buy("sh600519", price=1800, shares=100)

        assert result is True

    def test_simulate_buy_not_in_pool(self, system):
        """测试模拟买入 - 不在股票池"""
        system.stock_pool.positions = {}

        result = system.simulate_buy("sh600519")

        assert result is False

    def test_simulate_sell(self, system):
        """测试模拟卖出"""
        system.stock_pool.positions = {"sh600519": MagicMock(current_price=1800)}
        system.stock_pool.sell_stock.return_value = (True, "卖出成功")

        result = system.simulate_sell("sh600519", price=1900)

        assert result is True

    def test_run_backtest(self, system):
        """测试运行回测"""
        with patch('asset_lens.data.investment_system.strategy_engine') as mock_engine:
            system.current_strategy = "momentum"
            mock_backtest_result = MagicMock()
            system.backtester.run_backtest.return_value = mock_backtest_result

            historical_data = {"sh600519": [{"close": 1800}]}
            result = system.run_backtest(historical_data)

            assert result is not None

    def test_run_backtest_no_strategy(self, system):
        """测试运行回测 - 没有策略"""
        system.current_strategy = None

        with pytest.raises(ValueError):
            system.run_backtest({})

    def test_optimize_strategy(self, system):
        """测试优化策略"""
        with patch('asset_lens.data.investment_system.strategy_engine') as mock_engine:
            mock_engine.strategies = {"momentum": MagicMock(), "value": MagicMock()}
            mock_result = MagicMock()
            mock_result.sharpe_ratio = 1.5
            system.backtester.get_best_strategy.return_value = ("momentum", mock_result)
            system.set_strategy = MagicMock(return_value=True)

            historical_data = {"sh600519": [{"close": 1800}]}
            name, result = system.optimize_strategy(historical_data)

            assert name == "momentum"

    def test_get_system_status(self, system):
        """测试获取系统状态"""
        with patch('asset_lens.data.investment_system.strategy_engine') as mock_engine:
            mock_engine.strategies = {"momentum": MagicMock()}
            system.stock_pool.get_performance.return_value = {
                "total_stocks": 10,
                "watching_count": 5,
                "holding_count": 3,
                "sold_count": 2,
                "total_profit": 1000,
                "profit_rate": 0.1,
                "win_rate": 0.6,
            }

            result = system.get_system_status()

            assert result["system_name"] == "test_system"
            assert "stock_pool" in result
            assert "performance" in result

    def test_generate_report(self, system):
        """测试生成报告"""
        with patch('asset_lens.data.investment_system.strategy_engine') as mock_engine:
            mock_engine.strategies = {"momentum": MagicMock()}
            system.stock_pool.get_performance.return_value = {
                "total_stocks": 10,
                "watching_count": 5,
                "holding_count": 3,
                "sold_count": 2,
                "total_profit": 1000,
                "profit_rate": 0.1,
                "win_rate": 0.6,
                "win_count": 6,
                "lose_count": 4,
            }
            system.stock_pool.get_best_performers.return_value = []
            system.stock_pool.get_worst_performers.return_value = []
            system.stock_pool.list_stocks.return_value = []

            result = system.generate_report()

            assert "投资策略系统报告" in result
            assert "test_system" in result

    def test_export_data(self, system):
        """测试导出数据"""
        system.stock_pool.positions = {}
        system.stock_pool.history = []
        system.stock_pool.get_performance.return_value = {
            "total_stocks": 0,
            "profit_rate": 0,
        }

        result = system.export_data()

        assert result.exists()
