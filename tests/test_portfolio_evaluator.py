"""
Tests for strategy portfolio evaluator.
"""

import pytest

from asset_lens.strategy.portfolio_evaluator import StrategyPortfolioEvaluator


class MockStrategyEngine:
    """Mock strategy engine for testing"""

    def __init__(self):
        self.strategies = {
            "value": {"name": "value"},
            "momentum": {"name": "momentum"},
            "reversal": {"name": "reversal"},
        }

    def evaluate_stock(self, stock, strategy_name):
        """Mock evaluate stock"""
        return {
            "score": 0.8 if strategy_name == "value" else 0.5,
            "match": True,
            "matched_conditions": 2,
            "total_conditions": 3,
        }


class TestStrategyPortfolioEvaluator:
    """Test StrategyPortfolioEvaluator"""

    @pytest.fixture
    def evaluator(self):
        """Create evaluator instance"""
        engine = MockStrategyEngine()
        return StrategyPortfolioEvaluator(engine)

    def test_init(self, evaluator):
        """Test initialization"""
        assert evaluator.engine is not None

    def test_evaluate_strategy_portfolio_default_weights(self, evaluator):
        """Test evaluate with default weights"""
        stock = {"code": "sh600519", "name": "贵州茅台"}

        result = evaluator.evaluate_strategy_portfolio(stock)

        assert "combined_score" in result
        assert "strategies" in result
        assert "best_strategy" in result
        assert "recommendation" in result

    def test_evaluate_strategy_portfolio_custom_weights(self, evaluator):
        """Test evaluate with custom weights"""
        stock = {"code": "sh600519", "name": "贵州茅台"}
        weights = {"value": 0.5, "momentum": 0.5}

        result = evaluator.evaluate_strategy_portfolio(stock, weights)

        assert result["combined_score"] > 0
        assert "value" in result["strategies"]
        assert "momentum" in result["strategies"]

    def test_get_portfolio_recommendation(self, evaluator):
        """Test portfolio recommendation"""
        rec1 = evaluator._get_portfolio_recommendation(0.9, "value")
        assert "强烈推荐" in rec1

        rec2 = evaluator._get_portfolio_recommendation(0.7, "momentum")
        assert "推荐买入" in rec2

        rec3 = evaluator._get_portfolio_recommendation(0.5, "reversal")
        assert "观察" in rec3

        rec4 = evaluator._get_portfolio_recommendation(0.3, "value")
        assert "观望" in rec4

        rec5 = evaluator._get_portfolio_recommendation(0.1, None)
        assert "不建议" in rec5

    def test_screen_with_portfolio(self, evaluator):
        """Test screen with portfolio"""
        stocks = [
            {"code": "sh600519", "name": "贵州茅台"},
            {"code": "sz000001", "name": "平安银行"},
        ]

        results = evaluator.screen_with_portfolio(stocks, min_combined_score=0.0)

        assert len(results) == 2
        assert results[0]["combined_score"] >= results[1]["combined_score"]

    def test_screen_with_portfolio_min_score(self, evaluator):
        """Test screen with minimum score filter"""
        stocks = [
            {"code": "sh600519", "name": "贵州茅台"},
            {"code": "sz000001", "name": "平安银行"},
        ]

        results = evaluator.screen_with_portfolio(stocks, min_combined_score=1.0)

        assert len(results) == 0

    def test_empty_weights(self, evaluator):
        """Test with empty weights"""
        stock = {"code": "sh600519", "name": "贵州茅台"}

        result = evaluator.evaluate_strategy_portfolio(stock, {})

        assert result["combined_score"] == 0
        assert result["strategies"] == {}
