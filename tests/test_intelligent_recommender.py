"""
Tests for Intelligent Recommender
"""

import pytest
from unittest.mock import Mock, patch
from asset_lens.data.intelligent_recommender import (
    IntelligentRecommender,
    StrategyRecommendation,
    StockRecommendation,
)


@pytest.fixture
def recommender():
    """创建智能推荐器实例"""
    return IntelligentRecommender()


class TestStrategyRecommendation:
    """测试策略推荐结果"""

    def test_strategy_recommendation_creation(self):
        """测试创建策略推荐"""
        rec = StrategyRecommendation(
            strategy_name="value",
            score=85.0,
            reason="历史表现良好",
            expected_return=0.15,
            risk_level="low",
            confidence=0.8,
            historical_performance={"win_rate": 0.6},
        )

        assert rec.strategy_name == "value"
        assert rec.score == 85.0
        assert rec.reason == "历史表现良好"
        assert rec.expected_return == 0.15
        assert rec.risk_level == "low"
        assert rec.confidence == 0.8


class TestStockRecommendation:
    """测试股票推荐结果"""

    def test_stock_recommendation_creation(self):
        """测试创建股票推荐"""
        rec = StockRecommendation(
            code="sh600519",
            name="贵州茅台",
            score=90.0,
            reason="估值较低",
            strategy_match=["value"],
            risk_level="low",
            confidence=0.85,
            indicators={"pe_ratio": 12.0},
        )

        assert rec.code == "sh600519"
        assert rec.name == "贵州茅台"
        assert rec.score == 90.0
        assert rec.reason == "估值较低"
        assert rec.strategy_match == ["value"]
        assert rec.risk_level == "low"


class TestIntelligentRecommender:
    """测试智能推荐器"""

    def test_init(self, recommender):
        """测试初始化"""
        assert recommender.cache_path is not None
        assert recommender.recommendation_path is not None

    @patch("asset_lens.data.strategy_engine.strategy_engine")
    def test_recommend_strategy_no_strategies(self, mock_engine, recommender):
        """测试推荐策略 - 无策略"""
        mock_engine.list_strategies.return_value = []

        recommendations = recommender.recommend_strategy()

        assert isinstance(recommendations, list)
        assert len(recommendations) == 0

    @patch("asset_lens.data.strategy_engine.strategy_engine")
    def test_recommend_strategy_success(self, mock_engine, recommender):
        """测试推荐策略 - 成功"""
        mock_strategy = Mock()
        mock_strategy.name = "value"
        mock_strategy.stop_loss = -0.08
        mock_strategy.take_profit = 0.15
        mock_strategy.max_positions = 5
        mock_strategy.holding_period_max = 30

        mock_engine.list_strategies.return_value = [
            {"name": "value", "description": "价值策略"}
        ]
        mock_engine.get_strategy.return_value = mock_strategy
        mock_engine.validate_strategy.return_value = {
            "valid": True,
            "win_rate": 0.6,
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.1,
        }

        recommendations = recommender.recommend_strategy()

        assert isinstance(recommendations, list)
        assert all(isinstance(r, StrategyRecommendation) for r in recommendations)

    @patch("asset_lens.data.stock_screener.stock_screener")
    @patch("asset_lens.data.market_stock_fetcher.market_stock_fetcher")
    def test_recommend_stocks_no_stocks(
        self, mock_fetcher, mock_screener, recommender
    ):
        """测试推荐股票 - 无股票"""
        mock_fetcher.get_cached_market_stocks.return_value = []
        mock_screener.load_market_stocks.return_value = []

        recommendations = recommender.recommend_stocks()

        assert isinstance(recommendations, list)
        assert len(recommendations) == 0

    @patch("asset_lens.data.stock_screener.stock_screener")
    @patch("asset_lens.data.market_stock_fetcher.market_stock_fetcher")
    @patch("asset_lens.data.strategy_engine.strategy_engine")
    def test_recommend_stocks_success(
        self, mock_engine, mock_fetcher, mock_screener, recommender
    ):
        """测试推荐股票 - 成功"""
        mock_fetcher.get_cached_market_stocks.return_value = [
            {"code": "sh600519", "name": "贵州茅台", "pe_ratio": 12.0, "pb_ratio": 1.2}
        ]
        mock_screener.load_market_stocks.return_value = []
        mock_engine.evaluate_stock.return_value = {"match": False}

        recommendations = recommender.recommend_stocks(max_stocks=5, min_score=0)

        assert isinstance(recommendations, list)
        assert all(isinstance(r, StockRecommendation) for r in recommendations)

    def test_calculate_risk_compatibility_conservative(self, recommender):
        """测试风险兼容性 - 保守型"""
        mock_strategy = Mock()
        mock_strategy.stop_loss = -0.05
        mock_strategy.take_profit = 0.10
        mock_strategy.max_positions = 3

        score = recommender._calculate_risk_compatibility(
            mock_strategy, "conservative"
        )

        assert score > 0

    def test_calculate_risk_compatibility_aggressive(self, recommender):
        """测试风险兼容性 - 激进型"""
        mock_strategy = Mock()
        mock_strategy.stop_loss = -0.15
        mock_strategy.take_profit = 0.30
        mock_strategy.max_positions = 15

        score = recommender._calculate_risk_compatibility(
            mock_strategy, "aggressive"
        )

        assert score > 0

    def test_calculate_period_compatibility_short(self, recommender):
        """测试投资周期兼容性 - 短期"""
        mock_strategy = Mock()
        mock_strategy.holding_period_max = 10

        score = recommender._calculate_period_compatibility(mock_strategy, "short")

        assert score > 0

    def test_calculate_period_compatibility_long(self, recommender):
        """测试投资周期兼容性 - 长期"""
        mock_strategy = Mock()
        mock_strategy.holding_period_max = 60

        score = recommender._calculate_period_compatibility(mock_strategy, "long")

        assert score > 0

    def test_assess_strategy_risk_low(self, recommender):
        """测试评估策略风险 - 低风险"""
        mock_strategy = Mock()
        mock_strategy.stop_loss = -0.05
        mock_strategy.take_profit = 0.10
        mock_strategy.max_positions = 3

        risk = recommender._assess_strategy_risk(mock_strategy)

        assert risk == "low"

    def test_assess_strategy_risk_high(self, recommender):
        """测试评估策略风险 - 高风险"""
        mock_strategy = Mock()
        mock_strategy.stop_loss = -0.20
        mock_strategy.take_profit = 0.50
        mock_strategy.max_positions = 20

        risk = recommender._assess_strategy_risk(mock_strategy)

        assert risk == "high"

    def test_generate_strategy_reason(self, recommender):
        """测试生成策略推荐原因"""
        score = {
            "performance": {"win_rate": 0.6, "total_return": 0.15},
        }
        market_environment = {"market_type": "牛市"}

        reason = recommender._generate_strategy_reason(
            "value", score, market_environment
        )

        assert isinstance(reason, str)
        assert len(reason) > 0

    def test_generate_stock_reason(self, recommender):
        """测试生成股票推荐原因"""
        stock = {"code": "sh600519", "name": "贵州茅台"}
        score = {
            "indicators": {"pe_ratio": 12.0, "pb_ratio": 1.2},
            "strategy_match": ["value"],
        }
        market_environment = {"market_type": "牛市"}

        reason = recommender._generate_stock_reason(
            stock, score, market_environment
        )

        assert isinstance(reason, str)
        assert len(reason) > 0

    @patch("asset_lens.data.market_environment.market_environment_analyzer")
    def test_get_market_environment(self, mock_analyzer, recommender):
        """测试获取市场环境"""
        mock_env = Mock()
        mock_env.market_type = "牛市"
        mock_env.risk_level = "medium"
        mock_env.sentiment = "bullish"
        mock_analyzer.analyze_environment.return_value = mock_env

        env = recommender._get_market_environment()

        assert env["market_type"] == "牛市"
        assert env["risk_level"] == "medium"
        assert env["sentiment"] == "bullish"

    def test_save_recommendations(self, recommender, tmp_path):
        """测试保存推荐结果"""
        recommender.recommendation_path = tmp_path

        recs = [
            StrategyRecommendation(
                strategy_name="value",
                score=85.0,
                reason="测试",
                expected_return=0.15,
                risk_level="low",
                confidence=0.8,
                historical_performance={},
            )
        ]

        filepath = recommender.save_recommendations(recs, "test.json")

        assert filepath.endswith("test.json")
        import os

        assert os.path.exists(filepath)
