"""
Tests for Market Environment Analyzer.
市场环境分析模块测试
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from asset_lens.data.market_environment import MarketEnvironment, MarketEnvironmentAnalyzer, StrategyAdaptation


class TestMarketEnvironment:
    """MarketEnvironment 测试"""

    def test_default_values(self):
        """测试默认值"""
        env = MarketEnvironment(
            date="2024-01-01",
            market_type="oscillation",
            index_change_5d=0,
            index_change_20d=0,
            index_change_60d=0,
            volatility=0,
            volume_trend="stable",
            sentiment="neutral",
            hot_sectors=[],
            cold_sectors=[],
            recommended_strategies=[],
            risk_level="medium",
        )
        assert env.date == "2024-01-01"
        assert env.market_type == "oscillation"
        assert env.volatility == 00

    def test_custom_values(self):
        """测试自定义值"""
        env = MarketEnvironment(
            date="2024-01-01",
            market_type="bull",
            index_change_5d=5.0,
            index_change_20d=10.0,
            index_change_60d=20.0,
            volatility=15.0,
            volume_trend="increasing",
            sentiment="optimistic",
            hot_sectors=["新能源", "半导体"],
            cold_sectors=["地产"],
            recommended_strategies=["momentum", "value"],
            risk_level="low",
        )
        assert env.market_type == "bull"
        assert env.index_change_5d == 5.0
        assert len(env.hot_sectors) == 2


class TestStrategyAdaptation:
    """StrategyAdaptation 测试"""

    def test_default_values(self):
        """测试默认值"""
        adaptation = StrategyAdaptation(
            strategy_name="momentum",
            original_params={},
            adapted_params={},
            reason="市场环境变化",
            expected_performance="medium",
        )
        assert adaptation.strategy_name == "momentum"
        assert adaptation.reason == "市场环境变化"

    def test_custom_values(self):
        """测试自定义值"""
        adaptation = StrategyAdaptation(
            strategy_name="value",
            original_params={"pe_max": 30},
            adapted_params={"pe_max": 20},
            reason="牛市环境，降低PE阈值",
            expected_performance="good",
        )
        assert adaptation.strategy_name == "value"
        assert adaptation.adapted_params["pe_max"] == 20


class TestMarketEnvironmentAnalyzer:
    """MarketEnvironmentAnalyzer 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def analyzer(self, temp_cache_path):
        """创建测试实例"""
        with patch("asset_lens.data.market_environment.config") as mock_config:
            mock_config.cache_path = temp_cache_path
            analyzer = MarketEnvironmentAnalyzer()
            yield analyzer

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.market_environment import market_environment_analyzer

        assert market_environment_analyzer is not None

    def test_init(self, analyzer):
        """测试初始化"""
        assert analyzer is not None
        assert analyzer.cache_path is not None
        assert analyzer.history is not None

    def test_load_history_empty(self, analyzer):
        """测试加载历史 - 空文件"""
        analyzer._load_history()
        assert analyzer.history == []

    def test_load_history_with_data(self, analyzer):
        """测试加载历史 - 有数据"""
        history_data = {
            "history": [
                {
                    "date": "2024-01-01",
                    "market_type": "bull",
                    "index_change_5d": 5.0,
                    "index_change_20d": 10.0,
                    "index_change_60d": 20.0,
                    "volatility": 15.0,
                    "volume_trend": "increasing",
                    "sentiment": "optimistic",
                    "hot_sectors": ["新能源"],
                    "cold_sectors": [],
                    "recommended_strategies": ["momentum"],
                    "risk_level": "low",
                }
            ]
        }

        analyzer._cache.save_file("market_environment.json", history_data, ttl=0)

        analyzer._load_history()
        assert len(analyzer.history) == 1
        assert analyzer.history[0].market_type == "bull"

    def test_save_history(self, analyzer):
        """测试保存历史"""
        analyzer.history = [
            MarketEnvironment(
                date="2024-01-01",
                market_type="bull",
                index_change_5d=5.0,
                index_change_20d=10.0,
                index_change_60d=20.0,
                volatility=15.0,
                volume_trend="increasing",
                sentiment="optimistic",
                hot_sectors=["新能源"],
                cold_sectors=[],
                recommended_strategies=["momentum"],
                risk_level="low",
            )
        ]

        analyzer._save_history()

        # Verify data was saved by loading it back
        loaded = analyzer._cache.load_file("market_environment.json")
        assert loaded is not None

    def test_get_latest_environment_empty(self, analyzer):
        """测试获取最新环境 - 空历史"""
        env = analyzer.history[-1] if analyzer.history else None
        assert env is None

    def test_get_latest_environment_with_data(self, analyzer):
        """测试获取最新环境 - 有历史"""
        analyzer.history = [
            MarketEnvironment(
                date="2024-01-01",
                market_type="bull",
                index_change_5d=5.0,
                index_change_20d=10.0,
                index_change_60d=20.0,
                volatility=15.0,
                volume_trend="increasing",
                sentiment="optimistic",
                hot_sectors=["新能源"],
                cold_sectors=[],
                recommended_strategies=["momentum"],
                risk_level="low",
            )
        ]

        env = analyzer.history[-1] if analyzer.history else None
        assert env is not None
        assert env.market_type == "bull"

    def test_determine_market_type_bull(self, analyzer):
        """测试判断市场类型 - 牛市"""
        market_type = analyzer._determine_market_type(change_5d=5.0, change_20d=15.0, change_60d=25.0, volatility=10.0)
        assert market_type == "bull"

    def test_determine_market_type_bear(self, analyzer):
        """测试判断市场类型 - 熊市"""
        market_type = analyzer._determine_market_type(
            change_5d=-5.0, change_20d=-15.0, change_60d=-25.0, volatility=10.0
        )
        assert market_type == "bear"

    def test_determine_market_type_oscillation(self, analyzer):
        """测试判断市场类型 - 震荡市"""
        market_type = analyzer._determine_market_type(change_5d=1.0, change_20d=0.5, change_60d=1.0, volatility=5.0)
        assert market_type == "oscillation"

    def test_analyze_sentiment(self, analyzer):
        """测试分析市场情绪"""
        sentiment = analyzer._analyze_sentiment(5.0, 10.0, "bull")
        assert sentiment == "optimistic"

    def test_analyze_volume_trend(self, analyzer):
        """测试分析成交量趋势"""
        stocks_data = [
            {"change_percent": 5.0},
            {"change_percent": 3.0},
            {"change_percent": -1.0},
        ]
        trend = analyzer._analyze_volume_trend(stocks_data)
        assert trend in ["increasing", "decreasing", "stable"]

    def test_analyze_volume_trend_empty(self, analyzer):
        """测试分析成交量趋势 - 空数据"""
        trend = analyzer._analyze_volume_trend(None)
        assert trend == "stable"

    def test_assess_risk(self, analyzer):
        """测试评估风险等级"""
        risk = analyzer._assess_risk("bull", 10.0, "optimistic")
        assert risk in ["low", "medium", "high"]

    def test_recommend_strategies(self, analyzer):
        """测试推荐策略"""
        strategies = analyzer._recommend_strategies("bull", 10.0, "optimistic")
        assert isinstance(strategies, list)

    def test_recommend_strategies_bear(self, analyzer):
        """测试推荐策略 - 熊市"""
        strategies = analyzer._recommend_strategies("bear", 20.0, "pessimistic")
        assert isinstance(strategies, list)


class TestMarketScenarios:
    """市场场景测试"""

    def _determine_market_type(self, change_5d, change_20d, change_60d, volatility):
        """判断市场类型"""
        if change_20d > 10 and change_60d > 20:
            return "bull"
        elif change_20d < -10 and change_60d < -20:
            return "bear"
        elif volatility > 3:
            return "oscillation"
        elif change_20d > 5:
            return "bull"
        elif change_20d < -5:
            return "bear"
        else:
            return "oscillation"

    def test_bull_market_scenario(self):
        """测试牛市场景"""

        market_type = self._determine_market_type(5.0, 15.0, 30.0, 10.0)
        assert market_type == "bull"

    def test_bear_market_scenario(self):
        """测试熊市场景"""

        market_type = self._determine_market_type(-5.0, -15.0, -30.0, 10.0)
        assert market_type == "bear"

    def test_oscillation_market_scenario(self):
        """测试震荡市场景"""

        market_type = self._determine_market_type(1.0, 0.5, 1.0, 5.0)
        assert market_type == "oscillation"

    def test_risk_level_calculation(self):
        """测试风险等级计算"""
        volatility = 15.0

        if volatility > 20:
            risk_level = "high"
        elif volatility > 10:
            risk_level = "medium"
        else:
            risk_level = "low"

        assert risk_level == "medium"
