"""
Tests for Pre-market Analyzer.
盘前分析模块测试
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.analysis.premarket_analyzer import (
    PreMarketAnalyzer,
    PreMarketReport,
    MarketTrend,
    HotSector,
    StockAlert,
    premarket_analyzer,
)


class TestMarketTrend:
    """测试市场趋势数据类"""

    def test_create_market_trend(self):
        """测试创建市场趋势"""
        trend = MarketTrend(
            index_name="沪深300",
            current_value=4000.0,
            change_percent=1.5,
            trend="up",
            support_level=3900.0,
            resistance_level=4100.0,
        )

        assert trend.index_name == "沪深300"
        assert trend.current_value == 4000.0
        assert trend.change_percent == 1.5
        assert trend.trend == "up"
        assert trend.support_level == 3900.0
        assert trend.resistance_level == 4100.0

    def test_market_trend_defaults(self):
        """测试默认值"""
        trend = MarketTrend(
            index_name="上证50",
            current_value=3000.0,
            change_percent=-0.5,
            trend="down",
        )

        assert trend.support_level is None
        assert trend.resistance_level is None


class TestHotSector:
    """测试热点板块数据类"""

    def test_create_hot_sector(self):
        """测试创建热点板块"""
        sector = HotSector(
            name="AI算力",
            change_percent=3.5,
            leading_stocks=["寒武纪", "海光信息"],
            capital_inflow=50.2,
            reason="政策利好",
        )

        assert sector.name == "AI算力"
        assert sector.change_percent == 3.5
        assert len(sector.leading_stocks) == 2
        assert sector.capital_inflow == 50.2

    def test_hot_sector_default_reason(self):
        """测试默认原因"""
        sector = HotSector(
            name="新能源",
            change_percent=2.0,
            leading_stocks=["宁德时代"],
            capital_inflow=30.0,
        )

        assert sector.reason == ""


class TestStockAlert:
    """测试股票预警数据类"""

    def test_create_stock_alert(self):
        """测试创建股票预警"""
        alert = StockAlert(
            code="sh600519",
            name="贵州茅台",
            alert_type="announcement",
            title="业绩预告",
            content="预计净利润增长20%",
            impact="positive",
            date="2026-04-25",
        )

        assert alert.code == "sh600519"
        assert alert.alert_type == "announcement"
        assert alert.impact == "positive"


class TestPreMarketReport:
    """测试盘前报告数据类"""

    def test_create_pre_market_report(self):
        """测试创建盘前报告"""
        report = PreMarketReport(
            date="2026-04-25",
            overall_sentiment="bullish",
        )

        assert report.date == "2026-04-25"
        assert report.overall_sentiment == "bullish"
        assert len(report.market_trends) == 0
        assert len(report.hot_sectors) == 0
        assert len(report.alerts) == 0

    def test_pre_market_report_with_data(self):
        """测试带数据的盘前报告"""
        trends = [MarketTrend("沪深300", 4000.0, 1.0, "up")]
        sectors = [HotSector("AI", 3.0, ["股票A"], 50.0)]

        report = PreMarketReport(
            date="2026-04-25",
            market_trends=trends,
            hot_sectors=sectors,
            overall_sentiment="bullish",
        )

        assert len(report.market_trends) == 1
        assert len(report.hot_sectors) == 1


class TestPreMarketAnalyzer:
    """测试盘前分析器"""

    def test_init(self, tmp_path):
        """测试初始化"""
        analyzer = PreMarketAnalyzer(cache_path=tmp_path)
        assert analyzer.cache_path == tmp_path

    def test_identify_hot_sectors(self, tmp_path):
        """测试识别热点板块"""
        analyzer = PreMarketAnalyzer(cache_path=tmp_path)
        sectors = analyzer.identify_hot_sectors()

        assert len(sectors) > 0
        assert all(isinstance(s, HotSector) for s in sectors)

    def test_check_stock_alerts_empty_holdings(self, tmp_path):
        """测试空持仓的预警检查"""
        analyzer = PreMarketAnalyzer(cache_path=tmp_path)
        alerts = analyzer.check_stock_alerts(holdings=None)

        assert isinstance(alerts, list)
        assert len(alerts) == 0

    def test_generate_risk_warnings(self, tmp_path):
        """测试生成风险提示"""
        analyzer = PreMarketAnalyzer(cache_path=tmp_path)
        warnings = analyzer.generate_risk_warnings()

        assert len(warnings) > 0
        assert all(isinstance(w, str) for w in warnings)

    def test_generate_suggestions_bullish(self, tmp_path):
        """测试牛市建议生成"""
        analyzer = PreMarketAnalyzer(cache_path=tmp_path)

        trends = [
            MarketTrend("沪深300", 4000.0, 1.5, "up"),
            MarketTrend("上证50", 3000.0, 1.0, "up"),
            MarketTrend("创业板指", 2000.0, -0.5, "down"),
        ]
        sectors = [HotSector("AI", 3.0, ["股票A"], 50.0)]

        suggestions = analyzer.generate_suggestions(trends, sectors)

        assert len(suggestions) > 0
        assert any("偏强" in s for s in suggestions)

    def test_generate_suggestions_bearish(self, tmp_path):
        """测试熊市建议生成"""
        analyzer = PreMarketAnalyzer(cache_path=tmp_path)

        trends = [
            MarketTrend("沪深300", 4000.0, -1.5, "down"),
            MarketTrend("上证50", 3000.0, -1.0, "down"),
            MarketTrend("创业板指", 2000.0, 0.5, "up"),
        ]
        sectors = []

        suggestions = analyzer.generate_suggestions(trends, sectors)

        assert any("偏弱" in s for s in suggestions)

    def test_generate_suggestions_neutral(self, tmp_path):
        """测试震荡市建议生成"""
        analyzer = PreMarketAnalyzer(cache_path=tmp_path)

        trends = [
            MarketTrend("沪深300", 4000.0, 0.3, "up"),
            MarketTrend("上证50", 3000.0, 0.2, "up"),
        ]
        sectors = []

        suggestions = analyzer.generate_suggestions(trends, sectors)

        assert len(suggestions) > 0

    def test_generate_report(self, tmp_path):
        """测试生成完整报告"""
        analyzer = PreMarketAnalyzer(cache_path=tmp_path)

        report = analyzer.generate_report()

        assert isinstance(report, PreMarketReport)
        assert report.date == datetime.now().strftime("%Y-%m-%d")
        assert report.overall_sentiment in ["bullish", "bearish", "neutral"]
        assert len(report.hot_sectors) > 0
        assert len(report.risk_warnings) > 0
        assert len(report.suggestions) > 0

    def test_save_report(self, tmp_path):
        """测试保存报告"""
        analyzer = PreMarketAnalyzer(cache_path=tmp_path)

        report = PreMarketReport(
            date="2026-04-25",
            overall_sentiment="neutral",
        )

        analyzer._save_report(report)

        report_file = tmp_path / "premarket_2026-04-25.json"
        assert report_file.exists()

        with open(report_file, encoding="utf-8") as f:
            data = json.load(f)

        assert data["date"] == "2026-04-25"
        assert data["overall_sentiment"] == "neutral"

    def test_format_report(self, tmp_path):
        """测试格式化报告"""
        analyzer = PreMarketAnalyzer(cache_path=tmp_path)

        trends = [MarketTrend("沪深300", 4000.0, 1.5, "up")]
        sectors = [HotSector("AI", 3.0, ["股票A"], 50.0)]

        report = PreMarketReport(
            date="2026-04-25",
            market_trends=trends,
            hot_sectors=sectors,
            risk_warnings=["风险提示1"],
            suggestions=["建议1"],
            overall_sentiment="bullish",
        )

        formatted = analyzer.format_report(report)

        assert "盘前分析报告" in formatted
        assert "2026-04-25" in formatted
        assert "沪深300" in formatted
        assert "AI" in formatted


class TestPreMarketAnalyzerInstance:
    """测试全局实例"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert premarket_analyzer is not None
        assert isinstance(premarket_analyzer, PreMarketAnalyzer)
