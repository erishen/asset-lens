"""
Tests for Technical Indicators.
技术指标测试
"""

import pytest
from asset_lens.data.technical_indicators import TechnicalIndicators


class TestTechnicalIndicators:
    """技术指标测试"""

    @pytest.fixture
    def ti(self):
        """创建技术指标实例"""
        return TechnicalIndicators()

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.technical_indicators import TechnicalIndicators
        assert TechnicalIndicators is not None

    def test_calculate_rsi(self, ti):
        """测试 RSI 计算"""
        prices = [10, 11, 10, 12, 11, 13, 12, 14, 13, 15, 14, 16, 15, 17, 16]
        rsi = ti.calculate_rsi(prices, period=14)
        assert rsi is not None
        assert 0 <= rsi <= 100

    def test_calculate_rsi_all_gains(self, ti):
        """测试 RSI 全部上涨"""
        prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
        rsi = ti.calculate_rsi(prices, period=14)
        assert rsi == 100.0

    def test_calculate_boll(self, ti):
        """测试布林带计算"""
        prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                  19, 18, 17, 16, 15, 14, 13, 12, 11, 10]
        boll = ti.calculate_boll(prices, period=20, std_dev=2.0)
        assert boll is not None
        upper, middle, lower = boll
        assert upper > middle > lower

    def test_calculate_obv(self, ti):
        """测试 OBV 计算"""
        prices = [10, 11, 10, 12, 11]
        volumes = [1000, 1500, 1200, 2000, 1800]
        obv = ti.calculate_obv(prices, volumes)
        assert obv is not None
        assert isinstance(obv, float)

    def test_calculate_wr(self, ti):
        """测试 WR 计算"""
        high_prices = [15, 16, 17, 18, 19, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11]
        low_prices = [10, 11, 12, 13, 14, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6]
        close_prices = [12, 13, 14, 15, 16, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8]
        wr = ti.calculate_wr(high_prices, low_prices, close_prices, period=14)
        assert wr is not None
        assert -100 <= wr <= 0

    def test_calculate_atr(self, ti):
        """测试 ATR 计算"""
        high_prices = [15, 16, 17, 18, 19, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11]
        low_prices = [10, 11, 12, 13, 14, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6]
        close_prices = [12, 13, 14, 15, 16, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8]
        atr = ti.calculate_atr(high_prices, low_prices, close_prices, period=14)
        assert atr is not None
        assert atr > 0

    def test_get_rsi_signal(self, ti):
        """测试 RSI 信号"""
        assert ti.get_rsi_signal(75) == "sell"
        assert ti.get_rsi_signal(25) == "buy"
        assert ti.get_rsi_signal(50) == "hold"

    def test_get_boll_signal(self, ti):
        """测试布林带信号"""
        assert ti.get_boll_signal(105, 100, 95) == "sell"
        assert ti.get_boll_signal(90, 100, 95) == "buy"
        assert ti.get_boll_signal(97, 100, 95) == "hold"

    def test_get_wr_signal(self, ti):
        """测试威廉指标信号"""
        assert ti.get_wr_signal(-10) == "sell"
        assert ti.get_wr_signal(-90) == "buy"
        assert ti.get_wr_signal(-50) == "hold"
