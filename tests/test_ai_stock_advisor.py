"""
Tests for AI Stock Advisor
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from asset_lens.data.ai_stock_advisor import (
    AIStockAdvisor,
    StockAdvice,
    StrategyAdvice,
    MarketPrediction,
)


@pytest.fixture
def advisor():
    """创建 AI 顾问实例"""
    return AIStockAdvisor()


class TestStockAdvice:
    """测试股票建议数据类"""

    def test_stock_advice_creation(self):
        """测试创建股票建议"""
        advice = StockAdvice(
            code="sh600519",
            name="贵州茅台",
            action="buy",
            confidence=0.8,
            reasons=["估值较低", "技术指标良好"],
            risk_level="low",
            target_price=2000.0,
            stop_loss=1800.0,
            take_profit=2200.0,
            holding_period=30,
            position_size=0.1,
        )

        assert advice.code == "sh600519"
        assert advice.name == "贵州茅台"
        assert advice.action == "buy"
        assert advice.confidence == 0.8
        assert len(advice.reasons) == 2
        assert advice.risk_level == "low"
        assert advice.target_price == 2000.0

    def test_stock_advice_defaults(self):
        """测试股票建议默认值"""
        advice = StockAdvice(
            code="sh600519",
            name="贵州茅台",
            action="hold",
            confidence=0.5,
            reasons=["无明显信号"],
            risk_level="medium",
        )

        assert advice.target_price is None
        assert advice.stop_loss is None
        assert advice.take_profit is None
        assert advice.holding_period is None
        assert advice.position_size is None


class TestStrategyAdvice:
    """测试策略建议数据类"""

    def test_strategy_advice_creation(self):
        """测试创建策略建议"""
        advice = StrategyAdvice(
            strategy_name="value",
            action="use",
            confidence=0.7,
            reasons=["历史表现良好", "适合当前市场"],
            suggested_params={"stop_loss": -0.08},
            expected_return=0.15,
            risk_level="medium",
        )

        assert advice.strategy_name == "value"
        assert advice.action == "use"
        assert advice.confidence == 0.7
        assert len(advice.reasons) == 2
        assert advice.suggested_params == {"stop_loss": -0.08}
        assert advice.expected_return == 0.15

    def test_strategy_advice_defaults(self):
        """测试策略建议默认值"""
        advice = StrategyAdvice(
            strategy_name="momentum",
            action="avoid",
            confidence=0.3,
            reasons=["风险过高"],
        )

        assert advice.suggested_params == {}
        assert advice.expected_return == 0.0
        assert advice.risk_level == "medium"


class TestMarketPrediction:
    """测试市场预测数据类"""

    def test_market_prediction_creation(self):
        """测试创建市场预测"""
        prediction = MarketPrediction(
            market_type="bull",
            confidence=0.6,
            trend="up",
            volatility="medium",
            risk_factors=["估值偏高"],
            opportunities=["成长股机会"],
            suggested_actions=["增加权益配置"],
        )

        assert prediction.market_type == "bull"
        assert prediction.confidence == 0.6
        assert prediction.trend == "up"
        assert prediction.volatility == "medium"
        assert len(prediction.risk_factors) == 1
        assert len(prediction.opportunities) == 1
        assert len(prediction.suggested_actions) == 1


class TestAIStockAdvisor:
    """测试 AI 股票顾问"""

    def test_init(self, advisor):
        """测试初始化"""
        assert advisor.cache_path is not None
        assert advisor.advice_path is not None

    @patch("asset_lens.data.multi_source_fetcher.multi_source_fetcher")
    def test_generate_stock_advice_no_quote(self, mock_fetcher, advisor):
        """测试生成股票建议 - 无法获取行情"""
        mock_fetcher.fetch_stock_quote.return_value = None

        advice = advisor.generate_stock_advice("sh600519")

        assert advice.code == "sh600519"
        assert advice.action == "hold"
        assert advice.confidence == 0.0
        assert "无法获取股票数据" in advice.reasons

    @patch("asset_lens.data.multi_source_fetcher.multi_source_fetcher")
    @patch("asset_lens.data.strategy_engine.strategy_engine")
    def test_generate_stock_advice_buy_signal(self, mock_engine, mock_fetcher, advisor):
        """测试生成股票建议 - 买入信号"""
        mock_fetcher.fetch_stock_quote.return_value = {
            "code": "sh600519",
            "name": "贵州茅台",
            "current_price": 1800.0,
            "change_percent": 2.0,
            "pe_ratio": 12.0,
            "pb_ratio": 1.2,
        }

        mock_engine.list_strategies.return_value = []
        mock_engine.evaluate_stock.return_value = {"match": False}

        advice = advisor.generate_stock_advice("sh600519")

        assert advice.code == "sh600519"
        assert advice.name == "贵州茅台"
        assert advice.action in ["buy", "hold"]
        assert advice.confidence >= 0
        assert len(advice.reasons) > 0

    @patch("asset_lens.data.multi_source_fetcher.multi_source_fetcher")
    @patch("asset_lens.data.strategy_engine.strategy_engine")
    def test_generate_stock_advice_with_historical_data(
        self, mock_engine, mock_fetcher, advisor
    ):
        """测试生成股票建议 - 包含历史数据"""
        mock_fetcher.fetch_stock_quote.return_value = {
            "code": "sh600519",
            "name": "贵州茅台",
            "current_price": 1800.0,
            "change_percent": 2.0,
            "pe_ratio": 12.0,
            "pb_ratio": 1.2,
        }

        mock_engine.list_strategies.return_value = []
        mock_engine.evaluate_stock.return_value = {"match": False}

        historical_data = {
            "klines": [{"close": 1700.0 + i * 10} for i in range(30)]
        }

        advice = advisor.generate_stock_advice(
            "sh600519", historical_data=historical_data
        )

        assert advice.code == "sh600519"
        assert advice.action in ["buy", "sell", "hold"]

    @patch("asset_lens.data.strategy_engine.strategy_engine")
    def test_generate_strategy_advice_nonexistent(self, mock_engine, advisor):
        """测试生成策略建议 - 策略不存在"""
        mock_engine.get_strategy.return_value = None

        advice = advisor.generate_strategy_advice("nonexistent")

        assert advice.strategy_name == "nonexistent"
        assert advice.action == "avoid"
        assert advice.confidence == 0.0
        assert "策略不存在" in advice.reasons

    @patch("asset_lens.data.strategy_engine.strategy_engine")
    def test_generate_strategy_advice_success(self, mock_engine, advisor):
        """测试生成策略建议 - 成功"""
        mock_strategy = Mock()
        mock_strategy.name = "value"
        mock_strategy.stop_loss = -0.08
        mock_strategy.take_profit = 0.15
        mock_engine.get_strategy.return_value = mock_strategy
        mock_engine.validate_strategy.return_value = {
            "valid": True,
            "win_rate": 0.6,
            "total_return": 0.15,
        }

        advice = advisor.generate_strategy_advice("value")

        assert advice.strategy_name == "value"
        assert advice.action in ["use", "modify", "avoid"]
        assert advice.confidence >= 0

    @patch("asset_lens.data.market_environment.market_environment_analyzer")
    def test_predict_market(self, mock_analyzer, advisor):
        """测试市场预测"""
        mock_env = Mock()
        mock_env.market_type = "牛市"
        mock_env.risk_level = "medium"
        mock_env.sentiment = "bullish"
        mock_analyzer.analyze_environment.return_value = mock_env

        prediction = advisor.predict_market()

        assert prediction.market_type == "牛市"
        assert prediction.confidence >= 0
        assert prediction.trend in ["up", "down", "stable"]
        assert prediction.volatility in ["high", "medium", "low"]

    @patch("asset_lens.data.multi_source_fetcher.multi_source_fetcher")
    @patch("asset_lens.data.strategy_engine.strategy_engine")
    def test_batch_generate_advice(
        self, mock_engine, mock_fetcher, advisor
    ):
        """测试批量生成建议"""
        mock_fetcher.fetch_stock_quote.return_value = {
            "code": "sh600519",
            "name": "贵州茅台",
            "current_price": 1800.0,
            "change_percent": 2.0,
            "pe_ratio": 12.0,
            "pb_ratio": 1.2,
        }

        mock_engine.list_strategies.return_value = []
        mock_engine.evaluate_stock.return_value = {"match": False}

        codes = ["sh600519", "sz000001"]
        advices = advisor.batch_generate_advice(codes)

        assert len(advices) == 2
        assert all(isinstance(a, StockAdvice) for a in advices)

    @patch("asset_lens.data.stock_screener.stock_screener")
    @patch("asset_lens.data.multi_source_fetcher.multi_source_fetcher")
    @patch("asset_lens.data.strategy_engine.strategy_engine")
    def test_get_top_picks(
        self, mock_engine, mock_fetcher, mock_screener, advisor
    ):
        """测试获取热门推荐"""
        mock_screener.load_market_stocks.return_value = [
            {"code": "sh600519", "name": "贵州茅台"},
            {"code": "sz000001", "name": "平安银行"},
        ]

        mock_fetcher.fetch_stock_quote.return_value = {
            "code": "sh600519",
            "name": "贵州茅台",
            "current_price": 1800.0,
            "change_percent": 2.0,
            "pe_ratio": 12.0,
            "pb_ratio": 1.2,
        }

        mock_engine.list_strategies.return_value = []
        mock_engine.evaluate_stock.return_value = {"match": True, "score": 80}

        picks = advisor.get_top_picks(limit=5, min_confidence=0.0)

        assert isinstance(picks, list)
        assert all(isinstance(p, StockAdvice) for p in picks)

    def test_save_advice(self, advisor, tmp_path):
        """测试保存建议"""
        advisor.advice_path = tmp_path

        advice = StockAdvice(
            code="sh600519",
            name="贵州茅台",
            action="buy",
            confidence=0.8,
            reasons=["估值较低"],
            risk_level="low",
        )

        filepath = advisor.save_advice(advice, "test_advice.json")

        assert filepath.endswith("test_advice.json")
        import os

        assert os.path.exists(filepath)
