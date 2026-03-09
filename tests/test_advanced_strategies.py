"""
Tests for Advanced Strategies.
高级策略测试
"""

import pytest
from asset_lens.data.advanced_strategies import AdvancedStrategies


class TestMomentumStrategy:
    """动量策略测试"""

    def test_momentum_pass(self):
        """测试动量策略通过"""
        prices = [10, 11, 10, 12, 11, 13, 12, 14, 13, 15, 14, 16, 15, 17, 16, 17, 18, 19, 20, 19]
        volumes = [1000, 1500, 1200, 2000, 1800, 2200, 2000, 2500, 2300, 2800, 2600, 3000, 2800, 3200, 3000, 3500, 3300, 3800, 3600, 4000]
        result = AdvancedStrategies.momentum_strategy(
            prices, volumes, period=20, min_momentum=0.05
        )
        assert result["passed"] is True
        assert result["momentum"] >= 80.0

    def test_momentum_fail(self):
        """测试动量策略失败"""
        prices = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        volumes = [1000] * 10
        result = AdvancedStrategies.momentum_strategy(
            prices, volumes, period=10, min_momentum=0.05
        )
        assert result["passed"] is False

    def test_mean_reversion(self):
        """测试均值回归策略"""
        prices = [10, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        result = AdvancedStrategies.mean_reversion_strategy(
            prices, period=10, oversold_threshold=-0.1
        )
        assert result["passed"] is True

    def test_breakout(self):
        """测试突破策略"""
        prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
        volumes = [1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 5000]
        high_prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 29]
        result = AdvancedStrategies.breakout_strategy(
            prices, volumes, high_prices, period=20, volume_threshold=2.0
        )
        assert result["passed"] is True

    def test_value_strategy(self):
        """测试价值策略"""
        result = AdvancedStrategies.value_strategy(
            pe_ratio=10.0,
            pb_ratio=1.5,
            dividend_yield=0.05,
        )
        assert result["passed"] is True

    def test_growth_strategy(self):
        """测试成长策略"""
        result = AdvancedStrategies.growth_strategy(
            revenue_growth=0.3,
            profit_growth=0.25,
        )
        assert result["passed"] is True

    def test_quality_strategy(self):
        """测试质量策略"""
        result = AdvancedStrategies.quality_strategy(
            roe=0.2,
            debt_ratio=0.3,
            current_ratio=2.5,
        )
        assert result["passed"] is True

    def test_multi_factor_strategy(self):
        """测试多因子策略"""
        factors = {
            "momentum": 0.8,
            "value": 0.7,
            "growth": 0.6,
            "quality": 0.5,
            "technical": 0.4,
        }
        result = AdvancedStrategies.multi_factor_strategy(factors)
        assert result["passed"] is True
        assert result["score"] >= 0.6
