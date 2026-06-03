import pytest

from asset_lens.analysis.backtest_reporter import (
    BacktestMetrics,
    BacktestReport,
    BacktestReporter,
    ReportPeriod,
    StrategyComparison,
    StrategyGrade,
)


@pytest.fixture
def tmp_cache(tmp_path):
    return tmp_path / "backtest_test"


@pytest.fixture
def reporter(tmp_cache):
    return BacktestReporter(cache_path=tmp_cache)


class TestBacktestMetricsToDict:
    def test_to_dict(self):
        metrics = BacktestMetrics(
            total_return=0.15,
            annual_return=0.78,
            max_drawdown=0.08,
            sharpe_ratio=1.5,
            win_rate=0.6,
            profit_factor=2.0,
            total_trades=30,
            winning_trades=18,
            losing_trades=12,
            avg_profit=1500,
            avg_loss=800,
            avg_hold_days=7.5,
        )
        d = metrics.to_dict()
        assert d["total_return"] == 0.15
        assert d["sharpe_ratio"] == 1.5
        assert d["total_trades"] == 30
        assert d["winning_trades"] == 18


class TestStrategyComparisonToDict:
    def test_to_dict(self):
        metrics = BacktestMetrics(
            total_return=0.1,
            annual_return=0.5,
            max_drawdown=0.1,
            sharpe_ratio=1.0,
            win_rate=0.55,
            profit_factor=1.5,
            total_trades=20,
            winning_trades=11,
            losing_trades=9,
            avg_profit=1000,
            avg_loss=500,
            avg_hold_days=5,
        )
        comp = StrategyComparison(
            strategy_name="momentum",
            current_metrics=metrics,
            previous_metrics=None,
            improvement={},
            grade=StrategyGrade.B,
            rank=1,
        )
        d = comp.to_dict()
        assert d["strategy_name"] == "momentum"
        assert d["grade"] == "B"
        assert d["rank"] == 1
        assert d["previous_metrics"] is None
        assert isinstance(d["current_metrics"], dict)


class TestCalculateGrade:
    def test_grade_a(self, reporter):
        metrics = BacktestMetrics(
            total_return=0.25,
            annual_return=1.0,
            max_drawdown=0.05,
            sharpe_ratio=2.5,
            win_rate=0.65,
            profit_factor=2.5,
            total_trades=30,
            winning_trades=20,
            losing_trades=10,
            avg_profit=2000,
            avg_loss=500,
            avg_hold_days=5,
        )
        assert reporter._calculate_grade(metrics) == StrategyGrade.A

    def test_grade_f(self, reporter):
        metrics = BacktestMetrics(
            total_return=-0.15,
            annual_return=-0.5,
            max_drawdown=0.25,
            sharpe_ratio=0.2,
            win_rate=0.3,
            profit_factor=0.5,
            total_trades=20,
            winning_trades=6,
            losing_trades=14,
            avg_profit=500,
            avg_loss=1500,
            avg_hold_days=10,
        )
        assert reporter._calculate_grade(metrics) == StrategyGrade.F

    def test_grade_c(self, reporter):
        metrics = BacktestMetrics(
            total_return=0.05,
            annual_return=0.3,
            max_drawdown=0.12,
            sharpe_ratio=0.7,
            win_rate=0.52,
            profit_factor=1.2,
            total_trades=25,
            winning_trades=13,
            losing_trades=12,
            avg_profit=1000,
            avg_loss=800,
            avg_hold_days=7,
        )
        grade = reporter._calculate_grade(metrics)
        assert grade in (StrategyGrade.C, StrategyGrade.D, StrategyGrade.B)


class TestCalculateImprovement:
    def test_no_previous(self, reporter):
        metrics = BacktestMetrics(
            total_return=0.1,
            annual_return=0.5,
            max_drawdown=0.1,
            sharpe_ratio=1.0,
            win_rate=0.55,
            profit_factor=1.5,
            total_trades=20,
            winning_trades=11,
            losing_trades=9,
            avg_profit=1000,
            avg_loss=500,
            avg_hold_days=5,
        )
        result = reporter._calculate_improvement(metrics, None)
        assert result == {}

    def test_with_previous(self, reporter):
        current = BacktestMetrics(
            total_return=0.15,
            annual_return=0.78,
            max_drawdown=0.08,
            sharpe_ratio=1.5,
            win_rate=0.6,
            profit_factor=2.0,
            total_trades=30,
            winning_trades=18,
            losing_trades=12,
            avg_profit=1500,
            avg_loss=800,
            avg_hold_days=7,
        )
        previous = BacktestMetrics(
            total_return=0.10,
            annual_return=0.52,
            max_drawdown=0.12,
            sharpe_ratio=1.0,
            win_rate=0.55,
            profit_factor=1.5,
            total_trades=25,
            winning_trades=14,
            losing_trades=11,
            avg_profit=1200,
            avg_loss=900,
            avg_hold_days=6,
        )
        result = reporter._calculate_improvement(current, previous)
        assert "total_return" in result
        assert result["total_return"] == pytest.approx(0.05)
        assert "win_rate" in result
        assert "sharpe_ratio" in result


class TestGetPeriodRange:
    def test_daily(self, reporter):
        start, end = reporter._get_period_range(ReportPeriod.DAILY)
        assert start < end

    def test_weekly(self, reporter):
        start, end = reporter._get_period_range(ReportPeriod.WEEKLY)
        assert start < end

    def test_monthly(self, reporter):
        start, end = reporter._get_period_range(ReportPeriod.MONTHLY)
        assert start < end

    def test_quarterly(self, reporter):
        start, end = reporter._get_period_range(ReportPeriod.QUARTERLY)
        assert start < end

    def test_yearly(self, reporter):
        start, end = reporter._get_period_range(ReportPeriod.YEARLY)
        assert start < end


class TestGenerateReport:
    def test_generate_weekly(self, reporter):
        report = reporter.generate_report(period=ReportPeriod.WEEKLY)
        assert isinstance(report, BacktestReport)
        assert report.period == ReportPeriod.WEEKLY
        assert len(report.strategies) > 0
        assert report.best_strategy != ""
        assert report.overall_grade in list(StrategyGrade)

    def test_generate_with_custom_strategies(self, reporter):
        report = reporter.generate_report(strategies=["value", "momentum"])
        assert len(report.strategies) == 2
        strategy_names = [s.strategy_name for s in report.strategies]
        assert "value" in strategy_names
        assert "momentum" in strategy_names

    def test_strategies_sorted_by_return(self, reporter):
        report = reporter.generate_report()
        returns = [s.current_metrics.total_return for s in report.strategies]
        assert returns == sorted(returns, reverse=True)


class TestSaveAndLoadReports:
    def test_save_and_load(self, reporter):
        reporter.generate_report()
        reports = reporter._load_reports()
        assert len(reports) >= 1

    def test_get_recent_reports(self, reporter):
        reporter.generate_report()
        recent = reporter.get_recent_reports()
        assert len(recent) >= 1

    def test_corrupted_file(self, tmp_cache):
        cache = tmp_cache / "corrupted2"
        r = BacktestReporter(cache_path=cache)
        r.reports_file.parent.mkdir(parents=True, exist_ok=True)
        r.reports_file.write_text("bad json")
        reports = r._load_reports()
        assert reports == []


class TestGenerateRecommendations:
    def test_empty_comparisons(self, reporter):
        recs = reporter._generate_recommendations([])
        assert recs == ["暂无策略数据"]

    def test_with_negative_worst(self, reporter):
        good_metrics = BacktestMetrics(
            total_return=0.2,
            annual_return=1.0,
            max_drawdown=0.05,
            sharpe_ratio=2.0,
            win_rate=0.6,
            profit_factor=2.0,
            total_trades=30,
            winning_trades=18,
            losing_trades=12,
            avg_profit=2000,
            avg_loss=500,
            avg_hold_days=5,
        )
        bad_metrics = BacktestMetrics(
            total_return=-0.1,
            annual_return=-0.5,
            max_drawdown=0.2,
            sharpe_ratio=0.3,
            win_rate=0.35,
            profit_factor=0.8,
            total_trades=20,
            winning_trades=7,
            losing_trades=13,
            avg_profit=500,
            avg_loss=1500,
            avg_hold_days=10,
        )
        comparisons = [
            StrategyComparison("good", good_metrics, None, {}, StrategyGrade.A, 1),
            StrategyComparison("bad", bad_metrics, None, {}, StrategyGrade.F, 2),
        ]
        recs = reporter._generate_recommendations(comparisons)
        assert any("停用" in r for r in recs)


class TestFormatReport:
    def test_format(self, reporter):
        report = reporter.generate_report()
        text = reporter.format_report(report)
        assert "策略回测报告" in text
        assert "策略表现" in text
        assert "建议" in text


class TestCalculateOverallGrade:
    def test_empty_comparisons(self, reporter):
        assert reporter._calculate_overall_grade([]) == StrategyGrade.F

    def test_with_comparisons(self, reporter):
        metrics = BacktestMetrics(
            total_return=0.2,
            annual_return=1.0,
            max_drawdown=0.05,
            sharpe_ratio=2.0,
            win_rate=0.6,
            profit_factor=2.0,
            total_trades=30,
            winning_trades=18,
            losing_trades=12,
            avg_profit=2000,
            avg_loss=500,
            avg_hold_days=5,
        )
        comparisons = [
            StrategyComparison("a", metrics, None, {}, StrategyGrade.A, 1),
        ]
        grade = reporter._calculate_overall_grade(comparisons)
        assert grade in list(StrategyGrade)
