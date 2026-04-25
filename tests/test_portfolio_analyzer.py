"""
Tests for Portfolio Analyzer.
持仓分析模块测试
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from asset_lens.analysis.portfolio_analyzer import (
    PortfolioAnalyzer,
    PortfolioHealth,
    Position,
    StockDiagnosis,
    SectorAllocation,
    HealthLevel,
    TrendDirection,
    portfolio_analyzer,
)


class TestPosition:
    """测试持仓数据类"""

    def test_create_position(self):
        """测试创建持仓"""
        position = Position(
            code="sh600519",
            name="贵州茅台",
            shares=100,
            cost_price=1700.0,
            current_price=1800.0,
            market_value=180000.0,
            profit_loss=10000.0,
            profit_loss_percent=5.88,
            weight=25.0,
            industry="白酒",
        )

        assert position.code == "sh600519"
        assert position.shares == 100
        assert position.profit_loss == 10000.0
        assert position.weight == 25.0


class TestHealthLevel:
    """测试健康度等级枚举"""

    def test_health_levels(self):
        """测试所有健康度等级"""
        assert HealthLevel.EXCELLENT.value == "excellent"
        assert HealthLevel.GOOD.value == "good"
        assert HealthLevel.FAIR.value == "fair"
        assert HealthLevel.POOR.value == "poor"
        assert HealthLevel.CRITICAL.value == "critical"


class TestTrendDirection:
    """测试趋势方向枚举"""

    def test_trend_directions(self):
        """测试所有趋势方向"""
        assert TrendDirection.STRONG_UP.value == "strong_up"
        assert TrendDirection.UP.value == "up"
        assert TrendDirection.SIDEWAYS.value == "sideways"
        assert TrendDirection.DOWN.value == "down"
        assert TrendDirection.STRONG_DOWN.value == "strong_down"


class TestPortfolioAnalyzer:
    """测试持仓分析器"""

    def test_init(self, tmp_path):
        """测试初始化"""
        analyzer = PortfolioAnalyzer(cache_path=tmp_path)
        assert analyzer.cache_path == tmp_path

    def test_diagnose_stock(self, tmp_path):
        """测试个股诊断"""
        analyzer = PortfolioAnalyzer(cache_path=tmp_path)

        position = Position(
            code="sh600519",
            name="贵州茅台",
            shares=100,
            cost_price=1700.0,
            current_price=1800.0,
            market_value=180000.0,
            profit_loss=10000.0,
            profit_loss_percent=5.88,
            weight=15.0,
            industry="白酒",
        )

        diagnosis = analyzer.diagnose_stock(position)

        assert isinstance(diagnosis, StockDiagnosis)
        assert diagnosis.code == "sh600519"
        assert diagnosis.health_score > 0
        assert diagnosis.health_level in HealthLevel

    def test_diagnose_stock_with_technical_data(self, tmp_path):
        """测试带技术数据的诊断"""
        analyzer = PortfolioAnalyzer(cache_path=tmp_path)

        position = Position(
            code="sh600519",
            name="贵州茅台",
            shares=100,
            cost_price=1700.0,
            current_price=1800.0,
            market_value=180000.0,
            profit_loss=10000.0,
            profit_loss_percent=5.88,
            weight=15.0,
        )

        technical_data = {
            "rsi": 35,
            "macd_signal": "bullish",
            "ma_trend": "up",
        }

        diagnosis = analyzer.diagnose_stock(position, technical_data=technical_data)

        assert diagnosis.technical_score > 50

    def test_diagnose_stock_with_fundamental_data(self, tmp_path):
        """测试带基本面数据的诊断"""
        analyzer = PortfolioAnalyzer(cache_path=tmp_path)

        position = Position(
            code="sh600519",
            name="贵州茅台",
            shares=100,
            cost_price=1700.0,
            current_price=1800.0,
            market_value=180000.0,
            profit_loss=10000.0,
            profit_loss_percent=5.88,
            weight=15.0,
        )

        fundamental_data = {
            "pe_ratio": 25,
            "roe": 18,
            "revenue_growth": 15,
        }

        diagnosis = analyzer.diagnose_stock(position, fundamental_data=fundamental_data)

        assert diagnosis.fundamental_score > 50

    def test_analyze_portfolio_health_empty(self, tmp_path):
        """测试空持仓健康度"""
        analyzer = PortfolioAnalyzer(cache_path=tmp_path)

        health = analyzer.analyze_portfolio_health([])

        assert health.total_value == 0
        assert health.health_level == HealthLevel.CRITICAL

    def test_analyze_portfolio_health(self, tmp_path):
        """测试持仓健康度分析"""
        analyzer = PortfolioAnalyzer(cache_path=tmp_path)

        positions = [
            Position(
                code="sh600519",
                name="贵州茅台",
                shares=100,
                cost_price=1700.0,
                current_price=1800.0,
                market_value=180000.0,
                profit_loss=10000.0,
                profit_loss_percent=5.88,
                weight=30.0,
                industry="白酒",
            ),
            Position(
                code="sz000001",
                name="平安银行",
                shares=1000,
                cost_price=10.0,
                current_price=11.0,
                market_value=11000.0,
                profit_loss=1000.0,
                profit_loss_percent=10.0,
                weight=20.0,
                industry="银行",
            ),
            Position(
                code="sz000858",
                name="五粮液",
                shares=50,
                cost_price=160.0,
                current_price=170.0,
                market_value=8500.0,
                profit_loss=500.0,
                profit_loss_percent=6.25,
                weight=15.0,
                industry="白酒",
            ),
        ]

        health = analyzer.analyze_portfolio_health(positions)

        assert health.total_value > 0
        assert isinstance(health.health_score, float)
        assert health.health_level in HealthLevel
        assert len(health.top_positions) <= 5

    def test_analyze_portfolio_health_with_risk_positions(self, tmp_path):
        """测试有风险持仓的健康度"""
        analyzer = PortfolioAnalyzer(cache_path=tmp_path)

        positions = [
            Position(
                code="sh600519",
                name="贵州茅台",
                shares=100,
                cost_price=2000.0,
                current_price=1800.0,
                market_value=180000.0,
                profit_loss=-20000.0,
                profit_loss_percent=-10.0,
                weight=30.0,
            ),
            Position(
                code="sz000001",
                name="平安银行",
                shares=1000,
                cost_price=15.0,
                current_price=11.0,
                market_value=11000.0,
                profit_loss=-4000.0,
                profit_loss_percent=-26.67,
                weight=25.0,
            ),
        ]

        health = analyzer.analyze_portfolio_health(positions)

        assert len(health.risk_positions) >= 1

    def test_analyze_sector_allocation(self, tmp_path):
        """测试行业配置分析"""
        analyzer = PortfolioAnalyzer(cache_path=tmp_path)

        positions = [
            Position(
                code="sh600519",
                name="贵州茅台",
                shares=100,
                cost_price=1700.0,
                current_price=1800.0,
                market_value=180000.0,
                profit_loss=10000.0,
                profit_loss_percent=5.88,
                weight=50.0,
                industry="白酒",
                sector="消费",
            ),
            Position(
                code="sz000001",
                name="平安银行",
                shares=1000,
                cost_price=10.0,
                current_price=11.0,
                market_value=11000.0,
                profit_loss=1000.0,
                profit_loss_percent=10.0,
                weight=30.0,
                industry="银行",
                sector="金融",
            ),
        ]

        allocations = analyzer.analyze_sector_allocation(positions)

        assert len(allocations) >= 2
        assert allocations[0].weight >= allocations[1].weight

    def test_calculate_diversification(self, tmp_path):
        """测试分散度计算"""
        analyzer = PortfolioAnalyzer(cache_path=tmp_path)

        positions = [
            Position("sh600519", "茅台", 100, 1700, 1800, 180000, 10000, 5.88, 30),
            Position("sz000001", "平安", 1000, 10, 11, 11000, 1000, 10, 20),
            Position("sz000858", "五粮液", 50, 160, 170, 8500, 500, 6.25, 15),
        ]

        score = analyzer._calculate_diversification(positions)

        assert 0 <= score <= 100

    def test_calculate_concentration_risk(self, tmp_path):
        """测试集中度风险计算"""
        analyzer = PortfolioAnalyzer(cache_path=tmp_path)

        positions = [
            Position("sh600519", "茅台", 100, 1700, 1800, 180000, 10000, 5.88, 50),
            Position("sz000001", "平安", 1000, 10, 11, 11000, 1000, 10, 30),
        ]

        risk = analyzer._calculate_concentration_risk(positions)

        assert 0 <= risk <= 100

    def test_get_health_level(self, tmp_path):
        """测试健康度等级获取"""
        analyzer = PortfolioAnalyzer(cache_path=tmp_path)

        assert analyzer._get_health_level(85) == HealthLevel.EXCELLENT
        assert analyzer._get_health_level(70) == HealthLevel.GOOD
        assert analyzer._get_health_level(50) == HealthLevel.FAIR
        assert analyzer._get_health_level(30) == HealthLevel.POOR
        assert analyzer._get_health_level(10) == HealthLevel.CRITICAL

    def test_determine_trend(self, tmp_path):
        """测试趋势判断"""
        analyzer = PortfolioAnalyzer(cache_path=tmp_path)

        position = Position("sh600519", "茅台", 100, 1500, 1800, 180000, 30000, 20, 30)

        trend = analyzer._determine_trend(position, None)

        assert trend in [TrendDirection.STRONG_UP, TrendDirection.UP]

    def test_generate_suggestions(self, tmp_path):
        """测试建议生成"""
        analyzer = PortfolioAnalyzer(cache_path=tmp_path)

        position = Position(
            code="sh600519",
            name="贵州茅台",
            shares=100,
            cost_price=1500.0,
            current_price=1800.0,
            market_value=180000.0,
            profit_loss=30000.0,
            profit_loss_percent=20.0,
            weight=30.0,
        )

        suggestions = analyzer._generate_suggestions(position, 70, TrendDirection.UP)

        assert len(suggestions) > 0


class TestPortfolioAnalyzerInstance:
    """测试全局实例"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert portfolio_analyzer is not None
        assert isinstance(portfolio_analyzer, PortfolioAnalyzer)
