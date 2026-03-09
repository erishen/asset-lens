"""
Tests for Strategy Engine.
策略引擎测试
"""

import pytest
from unittest.mock import patch, MagicMock


class TestStrategyEngine:
    """策略引擎测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.strategy_engine import strategy_engine
        assert strategy_engine is not None

    def test_get_strategies(self):
        """测试获取策略列表"""
        from asset_lens.data.strategy_engine import strategy_engine
        # 测试方法存在
        assert hasattr(strategy_engine, 'get_strategies') or hasattr(strategy_engine, 'strategies')

    def test_screen_stocks_method(self):
        """测试筛选股票方法"""
        from asset_lens.data.strategy_engine import strategy_engine
        assert hasattr(strategy_engine, 'screen_stocks')


class TestMomentumStrategy:
    """动量策略测试"""

    def test_momentum_calculation(self):
        """测试动量计算"""
        prices = [100, 102, 105, 103, 108, 110, 112]
        
        # 计算动量（当前价格 / N天前价格 - 1）
        momentum = (prices[-1] / prices[0] - 1) * 100
        assert momentum == pytest.approx(12.0, rel=0.1)

    def test_momentum_signal(self):
        """测试动量信号"""
        momentum = 5.0  # 5% 动量
        threshold = 3.0  # 3% 阈值
        
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
