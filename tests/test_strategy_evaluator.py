"""
Tests for Strategy Evaluator - 策略评估器测试

覆盖边界场景:
- 空结果评估
- 收益指标计算
- 风险指标计算
- 因子贡献分析
- 可用性判定
"""

from asset_lens.trading.strategy_evaluator import FactorContribution, MarketStyle, StrategyEvaluator, StrategyUsability


class TestStrategyEvaluator:
    """策略评估器测试"""

    def test_empty_result_evaluation(self):
        """测试空结果评估"""
        evaluator = StrategyEvaluator()

        empty_result = {
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "win_rate": 0.0,
            "trades": [],
            "daily_values": [],
        }

        evaluation = evaluator.evaluate("test_strategy", empty_result)

        assert evaluation is not None

    def test_positive_return_evaluation(self):
        """测试正收益评估"""
        evaluator = StrategyEvaluator()

        result = {
            "total_return": 20.0,
            "annual_return": 25.0,
            "max_drawdown": 10.0,
            "sharpe_ratio": 1.5,
            "win_rate": 60.0,
            "trades": [
                {"action": "sell", "profit": 1000},
                {"action": "sell", "profit": -500},
                {"action": "sell", "profit": 800},
            ],
            "daily_values": [
                {"date": "2024-01-01", "total_value": 1000000},
                {"date": "2024-01-02", "total_value": 1050000},
                {"date": "2024-01-03", "total_value": 1200000},
            ],
        }

        evaluation = evaluator.evaluate("momentum_strategy", result)

        assert evaluation is not None

    def test_negative_return_evaluation(self):
        """测试负收益评估"""
        evaluator = StrategyEvaluator()

        result = {
            "total_return": -15.0,
            "annual_return": -20.0,
            "max_drawdown": 25.0,
            "sharpe_ratio": -0.5,
            "win_rate": 35.0,
            "trades": [
                {"action": "sell", "profit": -1000},
                {"action": "sell", "profit": -500},
                {"action": "sell", "profit": 200},
            ],
            "daily_values": [
                {"date": "2024-01-01", "total_value": 1000000},
                {"date": "2024-01-02", "total_value": 900000},
                {"date": "2024-01-03", "total_value": 850000},
            ],
        }

        evaluation = evaluator.evaluate("test_strategy", result)

        assert evaluation is not None

    def test_high_drawdown_evaluation(self):
        """测试高回撤评估"""
        evaluator = StrategyEvaluator()

        result = {
            "total_return": 10.0,
            "annual_return": 15.0,
            "max_drawdown": 35.0,
            "sharpe_ratio": 0.8,
            "win_rate": 50.0,
            "trades": [],
            "daily_values": [],
        }

        evaluation = evaluator.evaluate("test_strategy", result)

        assert evaluation is not None

    def test_low_sharpe_ratio_evaluation(self):
        """测试低夏普比率评估"""
        evaluator = StrategyEvaluator()

        result = {
            "total_return": 5.0,
            "annual_return": 8.0,
            "max_drawdown": 15.0,
            "sharpe_ratio": 0.3,
            "win_rate": 45.0,
            "trades": [],
            "daily_values": [],
        }

        evaluation = evaluator.evaluate("test_strategy", result)

        assert evaluation is not None

    def test_excellent_strategy_evaluation(self):
        """测试优秀策略评估"""
        evaluator = StrategyEvaluator()

        result = {
            "total_return": 30.0,
            "annual_return": 40.0,
            "max_drawdown": 8.0,
            "sharpe_ratio": 2.5,
            "win_rate": 70.0,
            "benchmark_return": 10.0,
            "excess_return": 20.0,
            "trades": [
                {"action": "sell", "profit": 5000},
                {"action": "sell", "profit": 3000},
                {"action": "sell", "profit": 2000},
            ],
            "daily_values": [
                {"date": "2024-01-01", "total_value": 1000000},
                {"date": "2024-01-02", "total_value": 1100000},
                {"date": "2024-01-03", "total_value": 1300000},
            ],
        }

        evaluation = evaluator.evaluate("excellent_strategy", result)

        assert evaluation is not None


class TestFactorContribution:
    """因子贡献分析测试"""

    def test_factor_contribution_creation(self):
        """测试因子贡献创建"""
        contribution = FactorContribution(
            factor_name="PE合理",
            category="fundamental",
            total_profit=5000.0,
            contribution_pct=25.0,
            win_rate=60.0,
            avg_return=5.0,
            correlation=0.8,
            importance_rank=1,
        )

        assert contribution.factor_name == "PE合理"
        assert contribution.total_profit == 5000.0
        assert contribution.contribution_pct == 25.0

    def test_factor_contribution_to_dict(self):
        """测试因子贡献转字典"""
        contribution = FactorContribution(
            factor_name="动量",
            category="technical",
            total_profit=3000.0,
            contribution_pct=15.0,
            win_rate=55.0,
            avg_return=3.0,
            correlation=0.6,
            importance_rank=2,
        )

        result = contribution.to_dict()

        assert "factor_name" in result
        assert "category" in result
        assert "total_profit" in result


class TestStrategyUsability:
    """策略可用性测试"""

    def test_usability_levels(self):
        """测试可用性级别"""
        assert StrategyUsability.EXCELLENT.value == "excellent"
        assert StrategyUsability.GOOD.value == "good"
        assert StrategyUsability.MODERATE.value == "moderate"
        assert StrategyUsability.POOR.value == "poor"
        assert StrategyUsability.UNUSABLE.value == "unusable"


class TestMarketStyle:
    """市场风格测试"""

    def test_market_style_values(self):
        """测试市场风格值"""
        assert MarketStyle.BULL.value == "bull"
        assert MarketStyle.BEAR.value == "bear"
        assert MarketStyle.SIDEWAYS.value == "sideways"
        assert MarketStyle.VOLATILE.value == "volatile"
