from asset_lens.analysis.review_models import (
    AttributionAnalysis,
    ClosedPosition,
    PerformanceMetrics,
    ReviewReport,
    ReviewTradeRecord,
    ReviewTradeResult,
    TradeType,
)


class TestTradeType:
    def test_values(self):
        assert TradeType.BUY.value == "buy"
        assert TradeType.SELL.value == "sell"
        assert TradeType.DIVIDEND.value == "dividend"
        assert TradeType.BONUS.value == "bonus"


class TestReviewTradeResult:
    def test_values(self):
        assert ReviewTradeResult.PROFIT.value == "profit"
        assert ReviewTradeResult.LOSS.value == "loss"
        assert ReviewTradeResult.BREAK_EVEN.value == "break_even"


class TestReviewTradeRecord:
    def test_creation(self):
        record = ReviewTradeRecord(
            code="600519",
            name="贵州茅台",
            trade_type=TradeType.BUY,
            shares=100,
            price=1800.0,
            amount=180000.0,
            commission=50.0,
            timestamp="2024-01-15 10:30:00",
        )
        assert record.code == "600519"
        assert record.trade_type == TradeType.BUY
        assert record.reason == ""
        assert record.strategy == ""

    def test_with_details(self):
        record = ReviewTradeRecord(
            code="600519",
            name="贵州茅台",
            trade_type=TradeType.SELL,
            shares=100,
            price=1900.0,
            amount=190000.0,
            commission=50.0,
            timestamp="2024-06-15 14:30:00",
            reason="止盈",
            strategy="趋势跟踪",
            notes="达到目标价",
        )
        assert record.reason == "止盈"
        assert record.strategy == "趋势跟踪"
        assert record.notes == "达到目标价"


class TestClosedPosition:
    def test_creation(self):
        pos = ClosedPosition(
            code="600519",
            name="贵州茅台",
            buy_price=1700.0,
            sell_price=1900.0,
            shares=100,
            profit_loss=20000.0,
            profit_loss_percent=11.76,
            hold_days=180,
            buy_date="2024-01-01",
            sell_date="2024-06-30",
        )
        assert pos.code == "600519"
        assert pos.profit_loss == 20000.0
        assert pos.result == ReviewTradeResult.PROFIT

    def test_loss(self):
        pos = ClosedPosition(
            code="600519",
            name="贵州茅台",
            buy_price=1900.0,
            sell_price=1700.0,
            shares=100,
            profit_loss=-20000.0,
            profit_loss_percent=-10.53,
            hold_days=90,
            buy_date="2024-01-01",
            sell_date="2024-04-01",
            result=ReviewTradeResult.LOSS,
        )
        assert pos.result == ReviewTradeResult.LOSS


class TestPerformanceMetrics:
    def test_creation(self):
        metrics = PerformanceMetrics(
            total_trades=20,
            winning_trades=14,
            losing_trades=6,
            win_rate=0.7,
            total_profit=50000.0,
            total_loss=20000.0,
            net_profit=30000.0,
            avg_profit=3571.43,
            avg_loss=3333.33,
            profit_factor=2.5,
            avg_hold_days=45.0,
            max_profit_trade=10000.0,
            max_loss_trade=5000.0,
        )
        assert metrics.total_trades == 20
        assert metrics.win_rate == 0.7
        assert metrics.sharpe_ratio == 0.0
        assert metrics.max_drawdown == 0.0

    def test_with_risk_metrics(self):
        metrics = PerformanceMetrics(
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=0.6,
            total_profit=30000.0,
            total_loss=15000.0,
            net_profit=15000.0,
            avg_profit=5000.0,
            avg_loss=3750.0,
            profit_factor=2.0,
            avg_hold_days=30.0,
            max_profit_trade=8000.0,
            max_loss_trade=4000.0,
            sharpe_ratio=1.5,
            max_drawdown=0.12,
        )
        assert metrics.sharpe_ratio == 1.5
        assert metrics.max_drawdown == 0.12


class TestAttributionAnalysis:
    def test_creation(self):
        closed = ClosedPosition(
            code="600519",
            name="贵州茅台",
            buy_price=1700.0,
            sell_price=1900.0,
            shares=100,
            profit_loss=20000.0,
            profit_loss_percent=11.76,
            hold_days=180,
            buy_date="2024-01-01",
            sell_date="2024-06-30",
        )
        attr = AttributionAnalysis(
            sector_contribution={"白酒": 0.15, "科技": -0.05},
            strategy_contribution={"趋势跟踪": 0.10, "均值回归": 0.05},
            time_contribution={"Q1": 0.08, "Q2": 0.07},
            top_winners=[closed],
            top_losers=[],
        )
        assert attr.sector_contribution["白酒"] == 0.15
        assert len(attr.top_winners) == 1


class TestReviewReport:
    def test_creation(self):
        metrics = PerformanceMetrics(
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=0.6,
            total_profit=30000.0,
            total_loss=15000.0,
            net_profit=15000.0,
            avg_profit=5000.0,
            avg_loss=3750.0,
            profit_factor=2.0,
            avg_hold_days=30.0,
            max_profit_trade=8000.0,
            max_loss_trade=4000.0,
        )
        attr = AttributionAnalysis(
            sector_contribution={},
            strategy_contribution={},
            time_contribution={},
            top_winners=[],
            top_losers=[],
        )
        report = ReviewReport(
            period_start="2024-01-01",
            period_end="2024-06-30",
            report_type="半年度",
            performance=metrics,
            attribution=attr,
            trades=[],
            closed_positions=[],
            suggestions=["减少高频交易"],
            lessons_learned=["止损要及时"],
            next_period_plan=["增加ETF配置"],
        )
        assert report.period_start == "2024-01-01"
        assert report.report_type == "半年度"
        assert len(report.suggestions) == 1
        assert report.timestamp is not None
