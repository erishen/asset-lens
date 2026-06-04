from asset_lens.analysis.portfolio_models import (
    HealthLevel,
    PortfolioHealth,
    Position,
    SectorAllocation,
    StockDiagnosis,
    TrendDirection,
)


class TestHealthLevel:
    def test_values(self):
        assert HealthLevel.EXCELLENT.value == "excellent"
        assert HealthLevel.GOOD.value == "good"
        assert HealthLevel.FAIR.value == "fair"
        assert HealthLevel.POOR.value == "poor"
        assert HealthLevel.CRITICAL.value == "critical"


class TestTrendDirection:
    def test_values(self):
        assert TrendDirection.STRONG_UP.value == "strong_up"
        assert TrendDirection.UP.value == "up"
        assert TrendDirection.SIDEWAYS.value == "sideways"
        assert TrendDirection.DOWN.value == "down"
        assert TrendDirection.STRONG_DOWN.value == "strong_down"


class TestPosition:
    def test_creation(self):
        pos = Position(
            code="600519",
            name="贵州茅台",
            shares=100,
            cost_price=1700.0,
            current_price=1800.0,
            market_value=180000.0,
            profit_loss=10000.0,
            profit_loss_percent=5.88,
            weight=0.3,
        )
        assert pos.code == "600519"
        assert pos.shares == 100
        assert pos.weight == 0.3

    def test_defaults(self):
        pos = Position(
            code="600519",
            name="贵州茅台",
            shares=100,
            cost_price=1700.0,
            current_price=1800.0,
            market_value=180000.0,
            profit_loss=10000.0,
            profit_loss_percent=5.88,
            weight=0.3,
        )
        assert pos.industry == ""
        assert pos.sector == ""


class TestStockDiagnosis:
    def test_creation(self):
        diag = StockDiagnosis(
            code="600519",
            name="贵州茅台",
            current_price=1800.0,
            trend=TrendDirection.UP,
            health_score=85.0,
            health_level=HealthLevel.GOOD,
        )
        assert diag.code == "600519"
        assert diag.health_score == 85.0
        assert diag.technical_score == 0.0
        assert diag.strengths == []
        assert diag.weaknesses == []

    def test_with_details(self):
        diag = StockDiagnosis(
            code="600519",
            name="贵州茅台",
            current_price=1800.0,
            trend=TrendDirection.STRONG_UP,
            health_score=90.0,
            health_level=HealthLevel.EXCELLENT,
            technical_score=85.0,
            fundamental_score=88.0,
            sentiment_score=92.0,
            strengths=["趋势强劲", "基本面优秀"],
            weaknesses=["估值偏高"],
            suggestions=["持有"],
            support_levels=[1750.0, 1700.0],
            resistance_levels=[1850.0, 1900.0],
        )
        assert len(diag.strengths) == 2
        assert len(diag.support_levels) == 2
        assert diag.fundamental_score == 88.0


class TestPortfolioHealth:
    def test_creation(self):
        pos = Position(
            code="600519",
            name="贵州茅台",
            shares=100,
            cost_price=1700.0,
            current_price=1800.0,
            market_value=180000.0,
            profit_loss=10000.0,
            profit_loss_percent=5.88,
            weight=0.5,
        )
        health = PortfolioHealth(
            total_value=360000.0,
            total_profit_loss=20000.0,
            total_profit_loss_percent=5.88,
            health_score=80.0,
            health_level=HealthLevel.GOOD,
            diversification_score=0.7,
            concentration_risk=0.3,
            sector_balance=0.6,
            top_positions=[pos],
            risk_positions=[],
        )
        assert health.total_value == 360000.0
        assert health.health_level == HealthLevel.GOOD
        assert len(health.top_positions) == 1
        assert health.suggestions == []


class TestSectorAllocation:
    def test_creation(self):
        pos = Position(
            code="600519",
            name="贵州茅台",
            shares=100,
            cost_price=1700.0,
            current_price=1800.0,
            market_value=180000.0,
            profit_loss=10000.0,
            profit_loss_percent=5.88,
            weight=0.3,
        )
        sector = SectorAllocation(
            sector="白酒",
            weight=0.3,
            profit_loss=10000.0,
            profit_loss_percent=5.88,
            positions=[pos],
        )
        assert sector.sector == "白酒"
        assert sector.weight == 0.3
        assert len(sector.positions) == 1
