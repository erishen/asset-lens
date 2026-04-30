"""
Tests for Trading Review.
复盘总结模块测试
"""

from asset_lens.analysis.trading_review import (
    ClosedPosition,
    PerformanceMetrics,
    TradeRecord,
    TradeResult,
    TradeType,
    TradingReview,
    trading_review,
)


class TestTradeType:
    """测试交易类型枚举"""

    def test_trade_types(self):
        """测试所有交易类型"""
        assert TradeType.BUY.value == "buy"
        assert TradeType.SELL.value == "sell"
        assert TradeType.DIVIDEND.value == "dividend"
        assert TradeType.BONUS.value == "bonus"


class TestTradeResult:
    """测试交易结果枚举"""

    def test_trade_results(self):
        """测试所有交易结果"""
        assert TradeResult.PROFIT.value == "profit"
        assert TradeResult.LOSS.value == "loss"
        assert TradeResult.BREAK_EVEN.value == "break_even"


class TestTradeRecord:
    """测试交易记录"""

    def test_create_trade_record(self):
        """测试创建交易记录"""
        record = TradeRecord(
            code="sh600519",
            name="贵州茅台",
            trade_type=TradeType.BUY,
            shares=100,
            price=1800.0,
            amount=180000.0,
            commission=50.0,
            timestamp="2024-01-15 09:30:00",
        )

        assert record.code == "sh600519"
        assert record.trade_type == TradeType.BUY
        assert record.amount == 180000.0


class TestClosedPosition:
    """测试已平仓记录"""

    def test_create_closed_position(self):
        """测试创建平仓记录"""
        position = ClosedPosition(
            code="sh600519",
            name="贵州茅台",
            buy_price=1800.0,
            sell_price=2000.0,
            shares=100,
            profit_loss=20000.0,
            profit_loss_percent=11.11,
            hold_days=30,
            buy_date="2024-01-01",
            sell_date="2024-01-31",
        )

        assert position.code == "sh600519"
        assert position.result == TradeResult.PROFIT
        assert position.profit_loss == 20000.0

    def test_closed_position_loss(self):
        """测试亏损平仓"""
        position = ClosedPosition(
            code="sh600519",
            name="贵州茅台",
            buy_price=2000.0,
            sell_price=1800.0,
            shares=100,
            profit_loss=-20000.0,
            profit_loss_percent=-10.0,
            hold_days=30,
            buy_date="2024-01-01",
            sell_date="2024-01-31",
            result=TradeResult.LOSS,
        )

        assert position.result == TradeResult.LOSS


class TestPerformanceMetrics:
    """测试绩效指标"""

    def test_create_performance_metrics(self):
        """测试创建绩效指标"""
        metrics = PerformanceMetrics(
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=60.0,
            total_profit=30000.0,
            total_loss=10000.0,
            net_profit=20000.0,
            avg_profit=5000.0,
            avg_loss=2500.0,
            profit_factor=3.0,
            avg_hold_days=15.0,
            max_profit_trade=8000.0,
            max_loss_trade=-3000.0,
        )

        assert metrics.total_trades == 10
        assert metrics.win_rate == 60.0
        assert metrics.profit_factor == 3.0


class TestTradingReview:
    """测试复盘总结器"""

    def test_init(self, tmp_path):
        """测试初始化"""
        review = TradingReview(cache_path=tmp_path)
        assert review.cache_path == tmp_path

    def test_record_trade(self, tmp_path):
        """测试记录交易"""
        review = TradingReview(cache_path=tmp_path)

        record = review.record_trade(
            code="sh600519",
            name="贵州茅台",
            trade_type=TradeType.BUY,
            shares=100,
            price=1800.0,
            reason="技术突破",
        )

        assert record.code == "sh600519"
        assert record.amount == 180000.0
        assert review.trades_file.exists()

    def test_record_closed_position(self, tmp_path):
        """测试记录平仓"""
        review = TradingReview(cache_path=tmp_path)

        position = review.record_closed_position(
            code="sh600519",
            name="贵州茅台",
            buy_price=1800.0,
            sell_price=2000.0,
            shares=100,
            buy_date="2024-01-01",
            sell_date="2024-01-31",
        )

        assert position.profit_loss == 20000.0
        assert position.hold_days == 30
        assert position.result == TradeResult.PROFIT

    def test_calculate_performance_empty(self, tmp_path):
        """测试计算空绩效"""
        review = TradingReview(cache_path=tmp_path)

        metrics = review.calculate_performance([])

        assert metrics.total_trades == 0
        assert metrics.win_rate == 0.0

    def test_calculate_performance_with_data(self, tmp_path):
        """测试计算绩效"""
        review = TradingReview(cache_path=tmp_path)

        positions = [
            ClosedPosition(
                code="sh600519",
                name="贵州茅台",
                buy_price=1800.0,
                sell_price=2000.0,
                shares=100,
                profit_loss=20000.0,
                profit_loss_percent=11.11,
                hold_days=30,
                buy_date="2024-01-01",
                sell_date="2024-01-31",
                result=TradeResult.PROFIT,
            ),
            ClosedPosition(
                code="sz000001",
                name="平安银行",
                buy_price=10.0,
                sell_price=9.0,
                shares=1000,
                profit_loss=-1000.0,
                profit_loss_percent=-10.0,
                hold_days=15,
                buy_date="2024-01-01",
                sell_date="2024-01-16",
                result=TradeResult.LOSS,
            ),
        ]

        metrics = review.calculate_performance(positions)

        assert metrics.total_trades == 2
        assert metrics.winning_trades == 1
        assert metrics.losing_trades == 1
        assert metrics.win_rate == 50.0
        assert metrics.net_profit == 19000.0

    def test_analyze_attribution(self, tmp_path):
        """测试归因分析"""
        review = TradingReview(cache_path=tmp_path)

        positions = [
            ClosedPosition(
                code="sh600519",
                name="贵州茅台",
                buy_price=1800.0,
                sell_price=2000.0,
                shares=100,
                profit_loss=20000.0,
                profit_loss_percent=11.11,
                hold_days=30,
                buy_date="2024-01-01",
                sell_date="2024-01-31",
                result=TradeResult.PROFIT,
            ),
        ]

        attribution = review.analyze_attribution(positions)

        assert "未知" in attribution.sector_contribution
        assert len(attribution.top_winners) == 1

    def test_generate_suggestions_low_win_rate(self, tmp_path):
        """测试生成建议 - 低胜率"""
        review = TradingReview(cache_path=tmp_path)

        metrics = PerformanceMetrics(
            total_trades=10,
            winning_trades=3,
            losing_trades=7,
            win_rate=30.0,
            total_profit=10000.0,
            total_loss=20000.0,
            net_profit=-10000.0,
            avg_profit=3333.0,
            avg_loss=2857.0,
            profit_factor=0.5,
            avg_hold_days=10.0,
            max_profit_trade=5000.0,
            max_loss_trade=-5000.0,
        )

        attribution = review.analyze_attribution([])

        suggestions = review.generate_suggestions(metrics, attribution)

        assert any("胜率" in s for s in suggestions)

    def test_generate_suggestions_good_profit_factor(self, tmp_path):
        """测试生成建议 - 高盈亏比"""
        review = TradingReview(cache_path=tmp_path)

        metrics = PerformanceMetrics(
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=60.0,
            total_profit=30000.0,
            total_loss=5000.0,
            net_profit=25000.0,
            avg_profit=5000.0,
            avg_loss=1250.0,
            profit_factor=6.0,
            avg_hold_days=10.0,
            max_profit_trade=8000.0,
            max_loss_trade=-2000.0,
        )

        attribution = review.analyze_attribution([])

        suggestions = review.generate_suggestions(metrics, attribution)

        assert any("盈亏比" in s for s in suggestions)

    def test_generate_lessons_learned(self, tmp_path):
        """测试生成经验教训"""
        review = TradingReview(cache_path=tmp_path)

        positions = [
            ClosedPosition(
                code="sh600519",
                name="贵州茅台",
                buy_price=1800.0,
                sell_price=2200.0,
                shares=100,
                profit_loss=40000.0,
                profit_loss_percent=22.22,
                hold_days=30,
                buy_date="2024-01-01",
                sell_date="2024-01-31",
                result=TradeResult.PROFIT,
            ),
        ]

        lessons = review.generate_lessons_learned(positions)

        assert len(lessons) > 0

    def test_generate_report(self, tmp_path):
        """测试生成报告"""
        review = TradingReview(cache_path=tmp_path)

        report = review.generate_report(report_type="weekly")

        assert report.report_type == "weekly"
        assert report.performance is not None
        assert report.suggestions is not None

    def test_format_report(self, tmp_path):
        """测试格式化报告"""
        review = TradingReview(cache_path=tmp_path)

        report = review.generate_report(report_type="weekly")
        formatted = review.format_report(report)

        assert "复盘报告" in formatted
        assert "绩效概览" in formatted


class TestTradingReviewInstance:
    """测试全局实例"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert trading_review is not None
        assert isinstance(trading_review, TradingReview)
