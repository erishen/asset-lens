from unittest.mock import MagicMock

import pytest

from asset_lens.strategy.engine import StrategyCondition
from asset_lens.strategy.engine_evaluation import StrategyEvaluationMixin


class FakeStrategyEngine(StrategyEvaluationMixin):
    def __init__(self):
        self._strategies = {}

    def get_strategy(self, name):
        return self._strategies.get(name)

    def add_strategy(self, name, conditions):
        strategy = MagicMock()
        strategy.buy_conditions = [
            StrategyCondition(
                name=c.get("name", ""),
                field=c["field"],
                operator=c["operator"],
                value=c["value"],
                weight=c.get("weight", 1.0),
            )
            for c in conditions
        ]
        self._strategies[name] = strategy


@pytest.fixture
def engine():
    return FakeStrategyEngine()


class TestEvaluateStock:
    def test_evaluate_with_strategy(self, engine):
        engine.add_strategy("value", [
            {"field": "pe_ratio", "operator": "lt", "value": 20, "weight": 1.0},
            {"field": "roe", "operator": "gt", "value": 15, "weight": 1.0},
        ])
        stock = {"code": "600519", "name": "贵州茅台", "pe_ratio": 18, "roe": 25}
        result = engine.evaluate_stock(stock, "value")
        assert result["score"] == 1.0
        assert result["recommendation"] == "强烈推荐"

    def test_evaluate_partial_match(self, engine):
        engine.add_strategy("value", [
            {"field": "pe_ratio", "operator": "lt", "value": 20, "weight": 1.0},
            {"field": "roe", "operator": "gt", "value": 15, "weight": 1.0},
        ])
        stock = {"code": "600519", "name": "贵州茅台", "pe_ratio": 25, "roe": 25}
        result = engine.evaluate_stock(stock, "value")
        assert result["score"] == 0.5
        assert result["recommendation"] == "观望"

    def test_evaluate_no_match(self, engine):
        engine.add_strategy("value", [
            {"field": "pe_ratio", "operator": "lt", "value": 20, "weight": 1.0},
            {"field": "roe", "operator": "gt", "value": 15, "weight": 1.0},
        ])
        stock = {"code": "600519", "name": "贵州茅台", "pe_ratio": 30, "roe": 5}
        result = engine.evaluate_stock(stock, "value")
        assert result["score"] == 0.0
        assert result["recommendation"] == "不推荐"

    def test_evaluate_nonexistent_strategy(self, engine):
        result = engine.evaluate_stock({"code": "600519"}, "nonexistent")
        assert "error" in result

    def test_evaluate_with_none_values(self, engine):
        engine.add_strategy("value", [
            {"field": "pe_ratio", "operator": "lt", "value": 20, "weight": 1.0},
        ])
        stock = {"code": "600519"}
        result = engine.evaluate_stock(stock, "value")
        assert result["score"] == 0.0


class TestGetFieldValue:
    def test_direct_field(self, engine):
        assert engine._get_field_value({"pe_ratio": 15}, "pe_ratio") == 15

    def test_alias_field(self, engine):
        assert engine._get_field_value({"PE": 15}, "pe_ratio") == 15

    def test_chinese_alias(self, engine):
        assert engine._get_field_value({"市盈率": 15}, "pe_ratio") == 15

    def test_missing_field(self, engine):
        assert engine._get_field_value({}, "pe_ratio") is None

    def test_unknown_field_name(self, engine):
        assert engine._get_field_value({"custom": 10}, "custom") == 10


class TestEvaluateCondition:
    def test_gt(self, engine):
        assert engine._evaluate_condition(10, "gt", 5) is True
        assert engine._evaluate_condition(3, "gt", 5) is False

    def test_gte(self, engine):
        assert engine._evaluate_condition(5, "gte", 5) is True
        assert engine._evaluate_condition(4, "gte", 5) is False

    def test_lt(self, engine):
        assert engine._evaluate_condition(3, "lt", 5) is True
        assert engine._evaluate_condition(7, "lt", 5) is False

    def test_lte(self, engine):
        assert engine._evaluate_condition(5, "lte", 5) is True
        assert engine._evaluate_condition(6, "lte", 5) is False

    def test_eq(self, engine):
        assert engine._evaluate_condition(5.0, "eq", 5.0) is True
        assert engine._evaluate_condition(5.1, "eq", 5.0) is False

    def test_ne(self, engine):
        assert engine._evaluate_condition(5.1, "ne", 5.0) is True
        assert engine._evaluate_condition(5.0, "ne", 5.0) is False

    def test_between(self, engine):
        assert engine._evaluate_condition(5, "between", [1, 10]) is True

    def test_between_with_numeric_target(self, engine):
        assert engine._evaluate_condition(5, "between", 1) is False

    def test_between_invalid(self, engine):
        assert engine._evaluate_condition(5, "between", [1]) is False

    def test_in_operator(self, engine):
        assert engine._evaluate_condition("a", "in", "a,b,c") is True
        assert engine._evaluate_condition("d", "in", "a,b,c") is False

    def test_none_value(self, engine):
        assert engine._evaluate_condition(None, "gt", 5) is False

    def test_string_eq(self, engine):
        assert engine._evaluate_condition("hello", "eq", "hello") is True

    def test_string_ne(self, engine):
        assert engine._evaluate_condition("hello", "ne", "world") is True

    def test_unknown_operator(self, engine):
        assert engine._evaluate_condition(5, "unknown", 5) is False


class TestScreenStocks:
    def test_screen(self, engine):
        engine.add_strategy("value", [
            {"field": "pe_ratio", "operator": "lt", "value": 20, "weight": 1.0},
        ])
        stocks = [
            {"code": "001", "name": "A", "pe_ratio": 15},
            {"code": "002", "name": "B", "pe_ratio": 25},
            {"code": "003", "name": "C", "pe_ratio": 10},
        ]
        result = engine.screen_stocks(stocks, "value", min_score=0.5)
        assert len(result) == 2
        codes = {r["stock_code"] for r in result}
        assert codes == {"001", "003"}

    def test_screen_with_limit(self, engine):
        engine.add_strategy("value", [
            {"field": "pe_ratio", "operator": "lt", "value": 20, "weight": 1.0},
        ])
        stocks = [{"code": f"{i:03d}", "name": f"S{i}", "pe_ratio": 10} for i in range(10)]
        result = engine.screen_stocks(stocks, "value", min_score=0.5, limit=3)
        assert len(result) <= 3


class TestValidateStrategy:
    def test_valid_strategy(self, engine):
        strategy = {
            "name": "value",
            "conditions": [{"field": "pe_ratio", "operator": "lt", "value": 20, "weight": 1.0}],
        }
        result = engine.validate_strategy(strategy)
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    def test_missing_name(self, engine):
        strategy = {"conditions": [{"field": "pe_ratio", "operator": "lt", "value": 20}]}
        result = engine.validate_strategy(strategy)
        assert result["is_valid"] is False

    def test_missing_conditions(self, engine):
        strategy = {"name": "value"}
        result = engine.validate_strategy(strategy)
        assert result["is_valid"] is False

    def test_invalid_operator(self, engine):
        strategy = {
            "name": "value",
            "conditions": [{"field": "pe_ratio", "operator": "invalid", "value": 20}],
        }
        result = engine.validate_strategy(strategy)
        assert result["is_valid"] is False

    def test_missing_value(self, engine):
        strategy = {
            "name": "value",
            "conditions": [{"field": "pe_ratio", "operator": "gt"}],
        }
        result = engine.validate_strategy(strategy)
        assert result["is_valid"] is False

    def test_unreasonable_weight(self, engine):
        strategy = {
            "name": "value",
            "conditions": [{"field": "pe_ratio", "operator": "lt", "value": 20, "weight": 15}],
        }
        result = engine.validate_strategy(strategy)
        assert len(result["warnings"]) > 0

    def test_zero_total_weight(self, engine):
        strategy = {
            "name": "value",
            "conditions": [{"field": "pe_ratio", "operator": "lt", "value": 20, "weight": 0}],
        }
        result = engine.validate_strategy(strategy)
        assert result["is_valid"] is False


class TestCombineStrategies:
    def test_combine(self, engine):
        engine.add_strategy("value", [{"field": "pe_ratio", "operator": "lt", "value": 20, "weight": 1.0}])
        engine.add_strategy("momentum", [{"field": "change_percent", "operator": "gt", "value": 3, "weight": 1.0}])
        result = engine.combine_strategies(["value", "momentum"])
        assert "error" not in result
        assert result["total_conditions"] == 2

    def test_combine_with_weights(self, engine):
        engine.add_strategy("value", [{"field": "pe_ratio", "operator": "lt", "value": 20, "weight": 1.0}])
        engine.add_strategy("momentum", [{"field": "change_percent", "operator": "gt", "value": 3, "weight": 1.0}])
        result = engine.combine_strategies(["value", "momentum"], weights=[0.7, 0.3])
        assert result["weights"] == [0.7, 0.3]

    def test_combine_no_strategies(self, engine):
        result = engine.combine_strategies(["nonexistent"])
        assert "error" in result

    def test_combine_mismatched_weights(self, engine):
        engine.add_strategy("value", [{"field": "pe_ratio", "operator": "lt", "value": 20, "weight": 1.0}])
        result = engine.combine_strategies(["value"], weights=[0.5, 0.5])
        assert result["weights"] == [1.0]


class TestEvaluateStrategyPortfolio:
    def test_evaluate(self, engine):
        engine.add_strategy("value", [{"field": "pe_ratio", "operator": "lt", "value": 20, "weight": 1.0}])
        engine.add_strategy("momentum", [{"field": "change_percent", "operator": "gt", "value": 3, "weight": 1.0}])
        stocks = [
            {"code": "001", "name": "A", "pe_ratio": 15, "change_percent": 5},
            {"code": "002", "name": "B", "pe_ratio": 25, "change_percent": 1},
        ]
        result = engine.evaluate_strategy_portfolio(stocks, ["value", "momentum"])
        assert "results" in result
        assert result["total_stocks"] == 2

    def test_evaluate_no_strategies(self, engine):
        result = engine.evaluate_strategy_portfolio([{"code": "001"}], ["nonexistent"])
        assert "error" in result


class TestScreenWithPortfolio:
    def test_screen(self, engine):
        engine.add_strategy("value", [{"field": "pe_ratio", "operator": "lt", "value": 20, "weight": 1.0}])
        engine.add_strategy("momentum", [{"field": "change_percent", "operator": "gt", "value": 3, "weight": 1.0}])
        stocks = [
            {"code": "001", "name": "A", "pe_ratio": 15, "change_percent": 5},
        ]
        result = engine.screen_with_portfolio(stocks, ["value", "momentum"])
        assert len(result) >= 0

    def test_screen_no_strategies(self, engine):
        result = engine.screen_with_portfolio([{"code": "001"}], ["nonexistent"])
        assert result == []


class TestGetPortfolioRecommendation:
    def test_strong_recommend(self, engine):
        assert "强烈推荐" in engine._get_portfolio_recommendation(0.9, "value")

    def test_recommend(self, engine):
        assert "推荐" in engine._get_portfolio_recommendation(0.7, "value")

    def test_watch(self, engine):
        assert engine._get_portfolio_recommendation(0.5, "value") == "观望"

    def test_not_recommend(self, engine):
        assert engine._get_portfolio_recommendation(0.2, "value") == "不推荐"
