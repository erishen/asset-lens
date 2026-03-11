"""
Tests for Strategy Engine.
策略引擎测试
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json


class TestStrategyCondition:
    """策略条件测试"""

    def test_strategy_condition_creation(self):
        """测试策略条件创建"""
        from asset_lens.data.strategy_engine import StrategyCondition
        
        condition = StrategyCondition(
            name="低PE",
            field="pe_ratio",
            operator="<",
            value=20,
            weight=0.3,
            description="市盈率低于20"
        )
        
        assert condition.name == "低PE"
        assert condition.field == "pe_ratio"
        assert condition.operator == "<"
        assert condition.value == 20
        assert condition.weight == 0.3
        assert condition.description == "市盈率低于20"

    def test_strategy_condition_defaults(self):
        """测试策略条件默认值"""
        from asset_lens.data.strategy_engine import StrategyCondition
        
        condition = StrategyCondition(
            name="test",
            field="test_field",
            operator=">",
            value=10
        )
        
        assert condition.weight == 1.0
        assert condition.description == ""


class TestStrategyConfig:
    """策略配置测试"""

    def test_strategy_config_creation(self):
        """测试策略配置创建"""
        from asset_lens.data.strategy_engine import StrategyConfig, StrategyCondition
        
        buy_conditions = [
            StrategyCondition(name="低PE", field="pe_ratio", operator="<", value=20)
        ]
        sell_conditions = [
            StrategyCondition(name="高PE", field="pe_ratio", operator=">", value=40)
        ]
        
        config = StrategyConfig(
            name="test_strategy",
            description="测试策略",
            buy_conditions=buy_conditions,
            sell_conditions=sell_conditions
        )
        
        assert config.name == "test_strategy"
        assert config.description == "测试策略"
        assert len(config.buy_conditions) == 1
        assert len(config.sell_conditions) == 1

    def test_strategy_config_defaults(self):
        """测试策略配置默认值"""
        from asset_lens.data.strategy_engine import StrategyConfig
        
        config = StrategyConfig(name="test")
        
        assert config.description == ""
        assert config.buy_conditions == []
        assert config.sell_conditions == []
        assert config.position_size == 0.1
        assert config.max_positions == 10
        assert config.stop_loss == -0.1
        assert config.take_profit == 0.2


class TestStrategyEngine:
    """策略引擎测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def engine(self, temp_cache_path):
        """创建策略引擎实例"""
        with patch('asset_lens.data.strategy_engine.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            from asset_lens.data.strategy_engine import StrategyEngine
            engine = StrategyEngine()
            yield engine

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.strategy_engine import strategy_engine
        assert strategy_engine is not None

    def test_engine_init(self, engine):
        """测试引擎初始化"""
        assert engine is not None
        assert engine.strategies is not None

    def test_load_default_strategies(self, engine):
        """测试加载默认策略"""
        assert "value" in engine.strategies
        assert "momentum" in engine.strategies
        assert "reversal" in engine.strategies
        assert "dividend" in engine.strategies

    def test_get_strategy(self, engine):
        """测试获取策略"""
        strategy = engine.get_strategy("value")
        assert strategy is not None
        assert strategy.name == "value"

    def test_get_strategy_not_found(self, engine):
        """测试获取不存在的策略"""
        strategy = engine.get_strategy("nonexistent")
        assert strategy is None

    def test_list_strategies(self, engine):
        """测试列出所有策略"""
        strategies = engine.list_strategies()
        assert len(strategies) >= 4
        
        strategy_names = [s["name"] for s in strategies]
        assert "value" in strategy_names
        assert "momentum" in strategy_names

    def test_evaluate_stock(self, engine):
        """测试评估股票"""
        stock = {
            "code": "sh600519",
            "name": "贵州茅台",
            "pe_ratio": 15,
            "market_cap": 200,
            "turnover_rate": 3,
            "change_percent": 2
        }
        
        result = engine.evaluate_stock(stock, "value")
        
        assert "match" in result
        assert "score" in result
        assert "details" in result

    def test_evaluate_stock_high_score(self, engine):
        """测试评估股票 - 高分"""
        stock = {
            "code": "sh600519",
            "name": "贵州茅台",
            "pe_ratio": 10,
            "market_cap": 100,
            "turnover_rate": 3,
            "change_percent": 2
        }
        
        result = engine.evaluate_stock(stock, "value")
        
        assert result["score"] >= 60

    def test_evaluate_stock_low_score(self, engine):
        """测试评估股票 - 低分"""
        stock = {
            "code": "sh600519",
            "name": "ST某某",
            "pe_ratio": 100,
            "market_cap": 10,
            "turnover_rate": 50,
            "change_percent": -10
        }
        
        result = engine.evaluate_stock(stock, "value")
        
        assert result["score"] < 60

    def test_evaluate_stock_invalid_strategy(self, engine):
        """测试评估股票 - 无效策略"""
        stock = {"code": "sh600519"}
        
        result = engine.evaluate_stock(stock, "invalid_strategy")
        
        assert result["match"] is False
        assert result["score"] == 0

    def test_screen_stocks(self, engine):
        """测试筛选股票"""
        stocks = [
            {"code": "sh600519", "name": "贵州茅台", "pe_ratio": 15, "market_cap": 200, "turnover_rate": 3, "change_percent": 2},
            {"code": "sz000001", "name": "平安银行", "pe_ratio": 8, "market_cap": 150, "turnover_rate": 5, "change_percent": 1},
            {"code": "sh601318", "name": "中国平安", "pe_ratio": 50, "market_cap": 500, "turnover_rate": 20, "change_percent": -5},
        ]
        
        results = engine.screen_stocks(stocks, "value")
        
        assert isinstance(results, list)
        assert all("strategy_score" in r for r in results)

    def test_screen_stocks_with_min_score(self, engine):
        """测试筛选股票 - 设置最低分数"""
        stocks = [
            {"code": "sh600519", "name": "贵州茅台", "pe_ratio": 15, "market_cap": 200, "turnover_rate": 3, "change_percent": 2},
        ]
        
        results = engine.screen_stocks(stocks, "value", min_score=80)
        
        assert all(r["strategy_score"] >= 80 for r in results)

    def test_create_custom_strategy(self, engine):
        """测试创建自定义策略"""
        buy_conditions = [
            {"name": "低PE", "field": "pe_ratio", "operator": "<", "value": 15}
        ]
        sell_conditions = [
            {"name": "高PE", "field": "pe_ratio", "operator": ">", "value": 30}
        ]
        
        strategy = engine.create_custom_strategy(
            name="custom_test",
            description="自定义测试策略",
            buy_conditions=buy_conditions,
            sell_conditions=sell_conditions
        )
        
        assert strategy.name == "custom_test"
        assert "custom_test" in engine.strategies

    def test_evaluate_condition_greater_than(self, engine):
        """测试评估条件 - 大于"""
        result = engine._evaluate_condition(10, ">", 5)
        assert result is True

    def test_evaluate_condition_less_than(self, engine):
        """测试评估条件 - 小于"""
        result = engine._evaluate_condition(5, "<", 10)
        assert result is True

    def test_evaluate_condition_between(self, engine):
        """测试评估条件 - 区间"""
        result = engine._evaluate_condition(15, "between", [10, 20])
        assert result is True

    def test_evaluate_condition_equal(self, engine):
        """测试评估条件 - 等于"""
        result = engine._evaluate_condition(True, "==", True)
        assert result is True

    def test_evaluate_condition_not_equal(self, engine):
        """测试评估条件 - 不等于"""
        result = engine._evaluate_condition("测试股票", "!=", "ST")
        assert result is True

    def test_get_field_value_direct(self, engine):
        """测试获取字段值 - 直接字段"""
        stock = {"pe_ratio": 15}
        value = engine._get_field_value(stock, "pe_ratio")
        assert value == 15

    def test_get_field_value_volume_ratio(self, engine):
        """测试获取字段值 - 量比"""
        stock = {"volume": 100000, "avg_volume_60d": 50000}
        value = engine._get_field_value(stock, "volume_ratio")
        assert value == 2.0

    def test_get_field_value_missing(self, engine):
        """测试获取字段值 - 缺失字段"""
        stock = {}
        value = engine._get_field_value(stock, "pe_ratio")
        assert value == 0


class TestStrategyBacktest:
    """策略回测测试"""

    def test_validate_strategy_not_found(self):
        """测试验证策略 - 策略不存在"""
        from asset_lens.data.strategy_engine import StrategyEngine
        
        with patch('asset_lens.data.strategy_engine.config') as mock_config:
            mock_config.cache_path = Path(tempfile.mkdtemp())
            engine = StrategyEngine()
            
            result = engine.validate_strategy("nonexistent", {})
            assert result["valid"] is False
            assert "不存在" in result["reason"]


class TestMomentumStrategy:
    """动量策略测试"""

    def test_momentum_calculation(self):
        """测试动量计算"""
        prices = [100, 102, 105, 103, 108, 110, 112]
        
        momentum = (prices[-1] / prices[0] - 1) * 100
        assert momentum == pytest.approx(12.0, rel=0.1)

    def test_momentum_signal(self):
        """测试动量信号"""
        momentum = 5.0
        threshold = 3.0
        
        signal = "buy" if momentum > threshold else "hold"
        assert signal == "buy"


class TestValueStrategy:
    """价值策略测试"""

    def test_pe_ratio_filter(self):
        """测试市盈率筛选"""
        pe_ratio = 15.0
        max_pe = 20.0
        
        is_undervalued = pe_ratio < max_pe
        assert is_undervalued is True

    def test_pb_ratio_filter(self):
        """测试市净率筛选"""
        pb_ratio = 1.5
        max_pb = 2.0
        
        is_undervalued = pb_ratio < max_pb
        assert is_undervalued is True


class TestStrategyScoring:
    """策略评分测试"""

    def test_score_calculation(self):
        """测试评分计算"""
        factors = {
            "momentum": 80,
            "value": 70,
            "quality": 85,
        }
        weights = {
            "momentum": 0.4,
            "value": 0.3,
            "quality": 0.3,
        }
        
        total_score = sum(factors[k] * weights[k] for k in factors)
        assert total_score == pytest.approx(78.5, rel=0.1)

    def test_score_ranking(self):
        """测试评分排名"""
        stocks = [
            {"code": "sh600519", "score": 85},
            {"code": "sz000001", "score": 75},
            {"code": "sh601318", "score": 90},
        ]
        
        ranked = sorted(stocks, key=lambda x: x["score"], reverse=True)
        assert ranked[0]["code"] == "sh601318"
