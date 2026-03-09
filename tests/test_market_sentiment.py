"""
Tests for Market Sentiment Analyzer.
市场风向分析器测试
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from asset_lens.core.market_sentiment import (
    MarketSentimentAnalyzer,
    SentimentIndicator,
    MarketSentiment,
    market_sentiment_analyzer,
)


class TestSentimentIndicator:
    """SentimentIndicator 测试"""

    def test_create_bullish_indicator(self):
        """测试创建看涨指标"""
        indicator = SentimentIndicator(
            name="指数趋势",
            value=75.0,
            level="bullish",
            description="强势上涨",
        )
        assert indicator.name == "指数趋势"
        assert indicator.value == 75.0
        assert indicator.level == "bullish"
        assert indicator.description == "强势上涨"

    def test_create_bearish_indicator(self):
        """测试创建看跌指标"""
        indicator = SentimentIndicator(
            name="板块热度",
            value=25.0,
            level="bearish",
            description="板块低迷",
        )
        assert indicator.level == "bearish"
        assert indicator.value == 25.0

    def test_create_neutral_indicator(self):
        """测试创建中性指标"""
        indicator = SentimentIndicator(
            name="资金流向",
            value=50.0,
            level="neutral",
            description="资金平稳",
        )
        assert indicator.level == "neutral"


class TestMarketSentiment:
    """MarketSentiment 测试"""

    def test_create_market_sentiment(self):
        """测试创建市场风向结果"""
        indicators = [
            SentimentIndicator("指数趋势", 70.0, "bullish", "上涨"),
            SentimentIndicator("板块热度", 60.0, "bullish", "活跃"),
        ]
        suggestions = ["建议加仓", "关注强势板块"]

        sentiment = MarketSentiment(
            overall_score=65.0,
            trend="bullish",
            risk_level="low",
            indicators=indicators,
            suggestions=suggestions,
            analysis_time="2026-03-09 12:00:00",
        )

        assert sentiment.overall_score == 65.0
        assert sentiment.trend == "bullish"
        assert sentiment.risk_level == "low"
        assert len(sentiment.indicators) == 2
        assert len(sentiment.suggestions) == 2


class TestMarketSentimentAnalyzer:
    """MarketSentimentAnalyzer 测试"""

    def test_analyzer_init(self):
        """测试分析器初始化"""
        analyzer = MarketSentimentAnalyzer()
        assert analyzer is not None
        assert "上证指数" in analyzer.index_weights
        assert "深证成指" in analyzer.index_weights

    def test_determine_trend_bullish(self):
        """测试趋势判断 - 看涨"""
        analyzer = MarketSentimentAnalyzer()
        assert analyzer._determine_trend(70.0) == "bullish"
        assert analyzer._determine_trend(65.0) == "bullish"

    def test_determine_trend_neutral(self):
        """测试趋势判断 - 中性"""
        analyzer = MarketSentimentAnalyzer()
        assert analyzer._determine_trend(50.0) == "neutral"
        assert analyzer._determine_trend(35.0) == "neutral"

    def test_determine_trend_bearish(self):
        """测试趋势判断 - 看跌"""
        analyzer = MarketSentimentAnalyzer()
        assert analyzer._determine_trend(30.0) == "bearish"
        assert analyzer._determine_trend(20.0) == "bearish"

    def test_determine_risk_level_low(self):
        """测试风险等级判断 - 低"""
        analyzer = MarketSentimentAnalyzer()
        indicators = [SentimentIndicator("test", 70.0, "bullish", "test")]
        assert analyzer._determine_risk_level(70.0, indicators) == "low"

    def test_determine_risk_level_medium(self):
        """测试风险等级判断 - 中"""
        analyzer = MarketSentimentAnalyzer()
        indicators = [SentimentIndicator("test", 50.0, "neutral", "test")]
        assert analyzer._determine_risk_level(50.0, indicators) == "medium"

    def test_determine_risk_level_high(self):
        """测试风险等级判断 - 高"""
        analyzer = MarketSentimentAnalyzer()
        indicators = [SentimentIndicator("test", 30.0, "bearish", "test")]
        assert analyzer._determine_risk_level(30.0, indicators) == "high"

    def test_generate_suggestions_bullish(self):
        """测试生成建议 - 看涨"""
        analyzer = MarketSentimentAnalyzer()
        indicators = [SentimentIndicator("指数趋势", 70.0, "bullish", "上涨")]
        suggestions = analyzer._generate_suggestions(70.0, indicators)
        assert len(suggestions) > 0
        assert any("乐观" in s or "增加" in s for s in suggestions)

    def test_generate_suggestions_bearish(self):
        """测试生成建议 - 看跌"""
        analyzer = MarketSentimentAnalyzer()
        indicators = [SentimentIndicator("指数趋势", 25.0, "bearish", "下跌")]
        suggestions = analyzer._generate_suggestions(25.0, indicators)
        assert len(suggestions) > 0
        assert any("悲观" in s or "降低" in s or "防守" in s for s in suggestions)

    def test_calculate_overall_score(self):
        """测试综合评分计算"""
        analyzer = MarketSentimentAnalyzer()
        indicators = [
            SentimentIndicator("指数趋势", 70.0, "bullish", "上涨"),
            SentimentIndicator("板块热度", 60.0, "bullish", "活跃"),
            SentimentIndicator("资金流向", 50.0, "neutral", "平稳"),
            SentimentIndicator("选股效果", 55.0, "neutral", "一般"),
            SentimentIndicator("成交量", 50.0, "neutral", "正常"),
        ]
        score = analyzer._calculate_overall_score(indicators)
        assert 0 <= score <= 100

    def test_get_report(self):
        """测试生成报告"""
        analyzer = MarketSentimentAnalyzer()
        report = analyzer.get_report()
        assert "市场风向分析报告" in report
        assert "综合评分" in report
        assert "市场趋势" in report
        assert "风险等级" in report
        assert "投资建议" in report

    def test_analyze_index_trend_success(self):
        """测试指数趋势分析 - 成功"""
        import requests
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'var hq_str_sh000001="上证指数,4000.00,4100.00,4200.00,4300.00,3900.00,100000,100000000,4200.00,4100.00,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1";'
        
        with patch("requests.get", return_value=mock_response):
            analyzer = MarketSentimentAnalyzer()
            indicator = analyzer._analyze_index_trend()
            assert indicator is not None
            assert indicator.name == "指数趋势"

    def test_analyze_index_trend_failure(self):
        """测试指数趋势分析 - 失败"""
        import requests
        with patch("requests.get", side_effect=Exception("Connection error")):
            analyzer = MarketSentimentAnalyzer()
            indicator = analyzer._analyze_index_trend()
            assert indicator.name == "指数趋势"
            assert indicator.level == "neutral"


class TestGlobalAnalyzer:
    """全局分析器实例测试"""

    def test_global_analyzer_exists(self):
        """测试全局分析器实例存在"""
        assert market_sentiment_analyzer is not None
        assert isinstance(market_sentiment_analyzer, MarketSentimentAnalyzer)
