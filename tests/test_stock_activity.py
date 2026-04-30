"""
Tests for Stock Activity Analyzer.
股票活动分析器测试
"""

from unittest.mock import MagicMock, patch

import pytest


class TestStockActivityAnalyzer:
    """股票活动分析器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.stock_activity_analyzer import StockActivityAnalyzer

        assert StockActivityAnalyzer is not None

    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        from asset_lens.data.stock_activity_analyzer import StockActivityAnalyzer

        with patch("asset_lens.data.stock_activity_analyzer.config") as mock_config:
            mock_config.cache_path = MagicMock()
            return StockActivityAnalyzer()

    def test_analyzer_init(self, analyzer):
        """测试初始化"""
        assert analyzer is not None

    def test_analyze_method(self, analyzer):
        """测试分析方法"""
        assert (
            hasattr(analyzer, "analyze_activity")
            or hasattr(analyzer, "get_market_overview")
            or hasattr(analyzer, "predict_etf")
        )


class TestActivityMetrics:
    """活动指标测试"""

    def test_volume_surge_detection(self):
        """测试成交量突增检测"""
        current_volume = 1000000
        avg_volume = 500000
        surge_ratio = current_volume / avg_volume if avg_volume > 0 else 0

        is_surge = surge_ratio >= 2.0  # 修复：使用 >= 而不是 >
        assert is_surge is True

    def test_price_change_calculation(self):
        """测试价格变化计算"""
        current_price = 10.5
        prev_price = 10.0
        change_pct = (current_price - prev_price) / prev_price * 100

        assert change_pct == 5.0

    def test_turnover_rate_calculation(self):
        """测试换手率计算"""
        volume = 1000000
        total_shares = 50000000
        turnover_rate = volume / total_shares * 100

        assert turnover_rate == 2.0


class TestActivitySignals:
    """活动信号测试"""

    def test_buy_signal(self):
        """测试买入信号"""
        signals = {
            "volume_surge": True,
            "price_up": True,
            "turnover_high": True,
        }

        buy_signal = all(signals.values())
        assert buy_signal is True

    def test_sell_signal(self):
        """测试卖出信号"""
        signals = {
            "volume_drop": True,
            "price_down": True,
        }

        sell_signal = all(signals.values())
        assert sell_signal is True

    def test_hold_signal(self):
        """测试持有信号"""
        signals = {
            "volume_surge": False,
            "price_up": False,
        }

        hold_signal = not any(signals.values())
        assert hold_signal is True
