"""
Tests for strategy_engine.py
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.data.strategy_engine import (
    StrategyCondition,
    StrategyConfig,
    StrategyEngine,
)


class TestStrategyCondition:
    """StrategyCondition 测试"""

    def test_default_values(self):
        """测试默认值"""
        condition = StrategyCondition(
            name="test_condition",
            field="pe_ratio",
            operator="<",
            value=20,
        )
        assert condition.name == "test_condition"
        assert condition.field == "pe_ratio"
        assert condition.operator == "<"
        assert condition.value == 20
        assert condition.weight == 1.0
        assert condition.description == ""

    def test_custom_values(self):
        """测试自定义值"""
        condition = StrategyCondition(
            name="pe_ratio",
            field="pe_ratio",
            operator="<",
            value=15.0,
            weight=0.5,
            description="市盈率低于15",
        )
        assert condition.name == "pe_ratio"
        assert condition.weight == 0.5
        assert condition.value == 15.0
        assert condition.description == "市盈率低于15"


class TestStrategyConfig:
    """StrategyConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        strategy = StrategyConfig(name="test_strategy")
        assert strategy.name == "test_strategy"
        assert strategy.description == ""
        assert strategy.buy_conditions == []
        assert strategy.sell_conditions == []
        assert strategy.position_size == 0.1
        assert strategy.max_positions == 10
        assert strategy.stop_loss == -0.1
        assert strategy.take_profit == 0.2

    def test_custom_values(self):
        """测试自定义值"""
        strategy = StrategyConfig(
            name="momentum",
            description="动量策略",
            buy_conditions=[
                StrategyCondition(name="volume", field="volume", operator=">", value=1000000),
            ],
            sell_conditions=[
                StrategyCondition(name="stop_loss", field="profit_rate", operator="<", value=-0.08),
            ],
            stop_loss=-0.08,
            take_profit=0.15,
        )
        assert strategy.name == "momentum"
        assert strategy.description == "动量策略"
        assert len(strategy.buy_conditions) == 1
        assert len(strategy.sell_conditions) == 1
        assert strategy.stop_loss == -0.08
        assert strategy.take_profit == 0.15


class TestStrategyEngine:
    """StrategyEngine 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def engine(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.data.strategy_engine.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            engine = StrategyEngine()
            yield engine

    def test_init(self, engine):
        """测试初始化"""
        assert engine.strategies_path.exists()
        assert isinstance(engine.strategies, dict)

    def test_default_strategies_loaded(self, engine):
        """测试默认策略已加载"""
        assert "value" in engine.strategies
        assert "momentum" in engine.strategies

    def test_get_strategy(self, engine):
        """测试获取策略"""
        result = engine.get_strategy("value")

        assert result is not None
        assert result.name == "value"

    def test_get_strategy_not_found(self, engine):
        """测试获取不存在的策略"""
        result = engine.get_strategy("not_exist")

        assert result is None

    def test_list_strategies(self, engine):
        """测试列出策略"""
        result = engine.list_strategies()

        assert len(result) >= 2
        strategy_names = [s["name"] for s in result]
        assert "value" in strategy_names
        assert "momentum" in strategy_names

    def test_create_strategy(self, engine):
        """测试创建策略"""
        strategy = StrategyConfig(
            name="test_strategy",
            description="测试策略",
        )

        engine.strategies["test_strategy"] = strategy

        assert "test_strategy" in engine.strategies
        assert engine.strategies["test_strategy"].description == "测试策略"

    def test_delete_strategy(self, engine):
        """测试删除策略"""
        engine.strategies["test_strategy"] = StrategyConfig(name="test_strategy")

        del engine.strategies["test_strategy"]

        assert "test_strategy" not in engine.strategies

    def test_screen_stocks_empty(self, engine):
        """测试筛选股票 - 空列表"""
        result = engine.screen_stocks([], "value")

        assert result == []

    def test_screen_stocks_with_data(self, engine):
        """测试筛选股票 - 有数据"""
        stocks = [
            {
                "code": "sh600519",
                "name": "贵州茅台",
                "pe_ratio": 15,
                "market_cap": 100,
                "turnover_rate": 3,
                "change_percent": 1,
                "current_price": 1800,
            },
        ]

        result = engine.screen_stocks(stocks, "value")

        assert isinstance(result, list)
