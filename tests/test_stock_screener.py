"""
Tests for stock_screener.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from asset_lens.data.stock_screener import (
    FundamentalConfig,
    ScoringWeights,
    ScreenerConfig,
    StockScreener,
    TechnicalConfig,
)


class TestFundamentalConfig:
    """FundamentalConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = FundamentalConfig()
        assert config.pe_max == 30.0
        assert config.pe_min == 0.0
        assert config.pb_max == 5.0
        assert config.pb_min == 0.0
        assert config.roe_min == 10.0
        assert config.revenue_growth_min == 0.0
        assert config.profit_growth_min == 0.0
        assert config.debt_ratio_max == 70.0
        assert config.market_cap_min == 20.0
        assert config.market_cap_max == 1000.0

    def test_custom_values(self):
        """测试自定义值"""
        config = FundamentalConfig(
            pe_max=50.0,
            pe_min=5.0,
            pb_max=10.0,
            pb_min=1.0,
            roe_min=15.0,
            revenue_growth_min=10.0,
            profit_growth_min=15.0,
            debt_ratio_max=50.0,
            market_cap_min=50.0,
            market_cap_max=500.0,
        )
        assert config.pe_max == 50.0
        assert config.pe_min == 5.0
        assert config.pb_max == 10.0
        assert config.pb_min == 1.0
        assert config.roe_min == 15.0
        assert config.revenue_growth_min == 10.0
        assert config.profit_growth_min == 15.0
        assert config.debt_ratio_max == 50.0
        assert config.market_cap_min == 50.0
        assert config.market_cap_max == 500.0


class TestTechnicalConfig:
    """TechnicalConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = TechnicalConfig()
        assert config.ma_trend is True
        assert config.macd_golden_cross is False
        assert config.rsi_oversold is False
        assert config.rsi_overbought is False
        assert config.rsi_min == 30.0
        assert config.rsi_max == 70.0
        assert config.volume_breakout is False
        assert config.volume_ratio_min == 2.0
        assert config.price_above_ma20 is False
        assert config.price_above_ma60 is False

    def test_custom_values(self):
        """测试自定义值"""
        config = TechnicalConfig(
            ma_trend=False,
            macd_golden_cross=True,
            rsi_oversold=True,
            rsi_min=20.0,
            rsi_max=80.0,
            volume_breakout=True,
            volume_ratio_min=3.0,
        )
        assert config.ma_trend is False
        assert config.macd_golden_cross is True
        assert config.rsi_oversold is True
        assert config.rsi_min == 20.0
        assert config.rsi_max == 80.0
        assert config.volume_breakout is True
        assert config.volume_ratio_min == 3.0


class TestScoringWeights:
    """ScoringWeights 测试"""

    def test_default_values(self):
        """测试默认值"""
        weights = ScoringWeights()
        assert weights.fundamental == 0.4
        assert weights.technical == 0.3
        assert weights.capital_flow == 0.2
        assert weights.industry == 0.1

    def test_custom_values(self):
        """测试自定义值"""
        weights = ScoringWeights(
            fundamental=0.5,
            technical=0.3,
            capital_flow=0.1,
            industry=0.1,
        )
        assert weights.fundamental == 0.5
        assert weights.technical == 0.3
        assert weights.capital_flow == 0.1
        assert weights.industry == 0.1


class TestScreenerConfig:
    """ScreenerConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = ScreenerConfig()
        assert config.max_results == 20
        assert config.min_score == 60.0
        assert isinstance(config.fundamental, FundamentalConfig)
        assert isinstance(config.technical, TechnicalConfig)
        assert isinstance(config.scoring_weights, ScoringWeights)

    def test_custom_values(self):
        """测试自定义值"""
        config = ScreenerConfig(
            max_results=50,
            min_score=70.0,
        )
        assert config.max_results == 50
        assert config.min_score == 70.0


class TestStockScreener:
    """StockScreener 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def screener(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.data.stock_screener.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            mock_config.project_root = temp_cache_path
            screener = StockScreener()
            yield screener

    def test_init(self, screener):
        """测试初始化"""
        assert screener.screener_config is not None
        assert screener.cache_path is not None

    def test_load_config_no_file(self, screener):
        """测试加载配置 - 文件不存在"""
        result = screener._load_config()

        assert isinstance(result, ScreenerConfig)
        assert result.max_results == 20

    def test_load_config_with_file(self, temp_cache_path):
        """测试加载配置 - 有文件"""
        config_dir = temp_cache_path / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "stock_screener.json"

        config_data = {
            "fundamental": {"pe_max": 50.0, "roe_min": 15.0},
            "technical": {"macd_golden_cross": True},
            "scoring_weights": {"fundamental": 0.5},
            "max_results": 30,
            "min_score": 70.0,
        }

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        new_screener = StockScreener(config_file)

        assert new_screener.screener_config.fundamental.pe_max == 50.0
        assert new_screener.screener_config.fundamental.roe_min == 15.0
        assert new_screener.screener_config.technical.macd_golden_cross is True
        assert new_screener.screener_config.max_results == 30
        assert new_screener.screener_config.min_score == 70.0

    def test_load_market_stocks_no_file(self, screener):
        """测试加载市场股票 - 文件不存在"""
        result = screener._load_market_stocks()

        assert result == []

    def test_load_market_stocks_with_file(self, screener, temp_cache_path):
        """测试加载市场股票 - 有文件"""
        market_stocks_file = temp_cache_path / "market_stocks.json"
        market_data = {
            "data": [
                {"code": "sh600519", "name": "贵州茅台", "pe_ratio": 25.0},
            ]
        }
        with open(market_stocks_file, "w", encoding="utf-8") as f:
            json.dump(market_data, f)

        screener.market_stocks_file = market_stocks_file
        screener._market_stocks = None
        result = screener._load_market_stocks()

        assert len(result) == 1
        assert result[0]["code"] == "sh600519"

    def test_filter_by_fundamental(self, screener):
        """测试基本面筛选"""
        stocks = [
            {"code": "sh600519", "name": "贵州茅台", "pe_ratio": 25.0, "pb_ratio": 3.0, "roe": 15.0, "market_cap": 100},
            {"code": "sh600000", "name": "浦发银行", "pe_ratio": 5.0, "pb_ratio": 0.5, "roe": 12.0, "market_cap": 80},
            {"code": "sh600001", "name": "邯郸钢铁", "pe_ratio": 50.0, "pb_ratio": 1.0, "roe": 5.0, "market_cap": 30},
        ]

        result = screener.filter_by_fundamental(stocks)

        assert isinstance(result, list)

    def test_filter_by_fundamental_empty(self, screener):
        """测试基本面筛选 - 空列表"""
        result = screener.filter_by_fundamental([])

        assert result == []

    def test_calculate_fundamental_score(self, screener):
        """测试计算基本面分数"""
        stock = {
            "code": "sh600519",
            "name": "贵州茅台",
            "pe_ratio": 25.0,
            "pb_ratio": 3.0,
            "roe": 15.0,
            "revenue_growth": 10.0,
            "profit_growth": 15.0,
            "debt_ratio": 30.0,
            "market_cap": 100,
        }

        result = screener._calculate_fundamental_score(stock)

        assert isinstance(result, float)
        assert result >= 0

    def test_calculate_comprehensive_score(self, screener):
        """测试计算综合分数"""
        stock = {
            "code": "sh600519",
            "name": "贵州茅台",
            "pe_ratio": 25.0,
            "pb_ratio": 3.0,
            "roe": 15.0,
            "revenue_growth": 10.0,
            "profit_growth": 15.0,
            "debt_ratio": 30.0,
            "market_cap": 100,
            "current_price": 1800.0,
        }

        result = screener.calculate_comprehensive_score(stock)

        assert isinstance(result, dict)
        assert "total_score" in result
        assert "fundamental_score" in result

    def test_screen_stocks_empty(self, screener):
        """测试筛选股票 - 空列表"""
        result = screener.screen([])

        assert result == []

    def test_screen_stocks_with_data(self, screener):
        """测试筛选股票 - 有数据"""
        stocks = [
            {
                "code": "sh600519",
                "name": "贵州茅台",
                "pe_ratio": 25.0,
                "pb_ratio": 3.0,
                "roe": 15.0,
                "market_cap": 100,
                "current_price": 1800.0,
            },
        ]

        result = screener.screen(stocks)

        assert isinstance(result, list)
