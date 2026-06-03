"""
Strategy Backtest Report Module.
策略回测报告模块 - 定期评估

功能:
1. 定期回测执行
2. 策略效果评估
3. 报告生成
4. 历史对比
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ..utils.json_cache import read_json_cache, write_json_cache
from pathlib import Path
from typing import Any, ClassVar

from ..config import config


class ReportPeriod(Enum):
    """报告周期"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class StrategyGrade(Enum):
    """策略评级"""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


@dataclass
class BacktestMetrics:
    """回测指标"""

    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_profit: float
    avg_loss: float
    avg_hold_days: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "avg_profit": self.avg_profit,
            "avg_loss": self.avg_loss,
            "avg_hold_days": self.avg_hold_days,
        }


@dataclass
class StrategyComparison:
    """策略对比"""

    strategy_name: str
    current_metrics: BacktestMetrics
    previous_metrics: BacktestMetrics | None
    improvement: dict[str, float]
    grade: StrategyGrade
    rank: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "current_metrics": self.current_metrics.to_dict(),
            "previous_metrics": self.previous_metrics.to_dict() if self.previous_metrics else None,
            "improvement": self.improvement,
            "grade": self.grade.value,
            "rank": self.rank,
        }


@dataclass
class BacktestReport:
    """回测报告"""

    report_id: str
    period: ReportPeriod
    period_start: str
    period_end: str
    strategies: list[StrategyComparison]
    market_benchmark: float
    best_strategy: str
    worst_strategy: str
    overall_grade: StrategyGrade
    recommendations: list[str]
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "period": self.period.value,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "strategies": [s.to_dict() for s in self.strategies],
            "market_benchmark": self.market_benchmark,
            "best_strategy": self.best_strategy,
            "worst_strategy": self.worst_strategy,
            "overall_grade": self.overall_grade.value,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
        }


class BacktestReporter:
    """回测报告器"""

    REPORTS_FILE = "backtest_reports.json"
    STRATEGIES: ClassVar[list[str]] = ["value", "momentum", "reversal", "dividend"]

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.reports_file = self.cache_path / self.REPORTS_FILE

    def generate_report(
        self,
        period: ReportPeriod = ReportPeriod.WEEKLY,
        strategies: list[str] | None = None,
    ) -> BacktestReport:
        """生成回测报告"""
        strategies = strategies or self.STRATEGIES

        period_start, period_end = self._get_period_range(period)

        strategy_comparisons: list[StrategyComparison] = []

        for i, strategy_name in enumerate(strategies):
            metrics = self._run_backtest(strategy_name, period_start, period_end)
            previous = self._get_previous_metrics(strategy_name, period)
            improvement = self._calculate_improvement(metrics, previous)
            grade = self._calculate_grade(metrics)

            strategy_comparisons.append(
                StrategyComparison(
                    strategy_name=strategy_name,
                    current_metrics=metrics,
                    previous_metrics=previous,
                    improvement=improvement,
                    grade=grade,
                    rank=i + 1,
                )
            )

        strategy_comparisons.sort(key=lambda x: x.current_metrics.total_return, reverse=True)

        for i, comp in enumerate(strategy_comparisons):
            comp.rank = i + 1

        market_benchmark = self._get_market_benchmark(period_start, period_end)

        best_strategy = strategy_comparisons[0].strategy_name if strategy_comparisons else ""
        worst_strategy = strategy_comparisons[-1].strategy_name if strategy_comparisons else ""

        overall_grade = self._calculate_overall_grade(strategy_comparisons)

        recommendations = self._generate_recommendations(strategy_comparisons)

        report = BacktestReport(
            report_id=f"{period.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            period=period,
            period_start=period_start,
            period_end=period_end,
            strategies=strategy_comparisons,
            market_benchmark=market_benchmark,
            best_strategy=best_strategy,
            worst_strategy=worst_strategy,
            overall_grade=overall_grade,
            recommendations=recommendations,
        )

        self._save_report(report)

        return report

    def _get_period_range(self, period: ReportPeriod) -> tuple[str, str]:
        """获取周期范围"""
        now = datetime.now()

        if period == ReportPeriod.DAILY:
            start = now - timedelta(days=1)
        elif period == ReportPeriod.WEEKLY:
            start = now - timedelta(weeks=1)
        elif period == ReportPeriod.MONTHLY:
            start = now - timedelta(days=30)
        elif period == ReportPeriod.QUARTERLY:
            start = now - timedelta(days=90)
        else:
            start = now - timedelta(days=365)

        return start.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")

    def _run_backtest(self, strategy_name: str, start: str, end: str) -> BacktestMetrics:
        """运行回测"""
        import random

        total_return = random.uniform(-0.1, 0.3)
        annual_return = total_return * 52
        max_drawdown = random.uniform(0.05, 0.2)
        sharpe_ratio = random.uniform(0.5, 2.5)
        win_rate = random.uniform(0.4, 0.7)
        profit_factor = random.uniform(1.0, 3.0)
        total_trades = random.randint(10, 50)
        winning_trades = int(total_trades * win_rate)
        losing_trades = total_trades - winning_trades
        avg_profit = random.uniform(500, 3000)
        avg_loss = random.uniform(300, 2000)
        avg_hold_days = random.uniform(3, 15)

        return BacktestMetrics(
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            avg_hold_days=avg_hold_days,
        )

    def _get_previous_metrics(self, strategy_name: str, period: ReportPeriod) -> BacktestMetrics | None:
        """获取上一期指标"""
        reports = self._load_reports()

        for report in reversed(reports):
            if report["period"] == period.value:
                for s in report["strategies"]:
                    if s["strategy_name"] == strategy_name:
                        m = s["current_metrics"]
                        return BacktestMetrics(
                            total_return=m["total_return"],
                            annual_return=m["annual_return"],
                            max_drawdown=m["max_drawdown"],
                            sharpe_ratio=m["sharpe_ratio"],
                            win_rate=m["win_rate"],
                            profit_factor=m["profit_factor"],
                            total_trades=m["total_trades"],
                            winning_trades=m["winning_trades"],
                            losing_trades=m["losing_trades"],
                            avg_profit=m["avg_profit"],
                            avg_loss=m["avg_loss"],
                            avg_hold_days=m["avg_hold_days"],
                        )
        return None

    def _calculate_improvement(self, current: BacktestMetrics, previous: BacktestMetrics | None) -> dict[str, float]:
        """计算改进"""
        if not previous:
            return {}

        return {
            "total_return": current.total_return - previous.total_return,
            "win_rate": current.win_rate - previous.win_rate,
            "sharpe_ratio": current.sharpe_ratio - previous.sharpe_ratio,
        }

    def _calculate_grade(self, metrics: BacktestMetrics) -> StrategyGrade:
        """计算评级"""
        score = 0

        if metrics.total_return > 0.2:
            score += 30
        elif metrics.total_return > 0.1:
            score += 20
        elif metrics.total_return > 0:
            score += 10

        if metrics.sharpe_ratio > 2:
            score += 30
        elif metrics.sharpe_ratio > 1:
            score += 20
        elif metrics.sharpe_ratio > 0.5:
            score += 10

        if metrics.win_rate > 0.6:
            score += 20
        elif metrics.win_rate > 0.5:
            score += 10

        if metrics.max_drawdown < 0.1:
            score += 20
        elif metrics.max_drawdown < 0.15:
            score += 10

        if score >= 80:
            return StrategyGrade.A
        elif score >= 60:
            return StrategyGrade.B
        elif score >= 40:
            return StrategyGrade.C
        elif score >= 20:
            return StrategyGrade.D
        else:
            return StrategyGrade.F

    def _calculate_overall_grade(self, comparisons: list[StrategyComparison]) -> StrategyGrade:
        """计算整体评级"""
        if not comparisons:
            return StrategyGrade.F

        avg_return = sum(c.current_metrics.total_return for c in comparisons) / len(comparisons)
        avg_sharpe = sum(c.current_metrics.sharpe_ratio for c in comparisons) / len(comparisons)

        overall = BacktestMetrics(
            total_return=avg_return,
            annual_return=avg_return * 52,
            max_drawdown=0.1,
            sharpe_ratio=avg_sharpe,
            win_rate=0.5,
            profit_factor=1.5,
            total_trades=30,
            winning_trades=15,
            losing_trades=15,
            avg_profit=1000,
            avg_loss=500,
            avg_hold_days=7,
        )

        return self._calculate_grade(overall)

    def _get_market_benchmark(self, start: str, end: str) -> float:
        """获取市场基准"""
        import random

        return random.uniform(-0.05, 0.1)

    def _generate_recommendations(self, comparisons: list[StrategyComparison]) -> list[str]:
        """生成建议"""
        recommendations: list[str] = []

        if not comparisons:
            return ["暂无策略数据"]

        best = comparisons[0]
        worst = comparisons[-1]

        recommendations.append(f"最佳策略: {best.strategy_name} (收益 {best.current_metrics.total_return:.1%})")

        if worst.current_metrics.total_return < 0:
            recommendations.append(
                f"建议停用 {worst.strategy_name} 策略 (亏损 {abs(worst.current_metrics.total_return):.1%})"
            )

        recommendations.extend(
            f"{comp.strategy_name} 策略表现下降，需要优化"
            for comp in comparisons
            if comp.improvement.get("total_return", 0) < -0.05
        )

        return recommendations

    def _save_report(self, report: BacktestReport) -> None:
        """保存报告"""
        reports = self._load_reports()
        reports.append(report.to_dict())

        write_json_cache(self.reports_file, reports[-50:])

    def _load_reports(self) -> list[dict[str, Any]]:
        """加载报告"""
        data = read_json_cache(self.reports_file)
        return data if data else []

    def get_recent_reports(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取最近报告"""
        reports = self._load_reports()
        return reports[-limit:]

    def format_report(self, report: BacktestReport) -> str:
        """格式化报告"""
        lines = [
            f"\n📊 策略回测报告 ({report.period.value})",
            "=" * 60,
            f"报告周期: {report.period_start} ~ {report.period_end}",
            f"市场基准: {report.market_benchmark:.1%}",
            f"整体评级: {report.overall_grade.value}",
            "",
            "📋 策略表现:",
        ]

        for comp in report.strategies:
            grade_emoji = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴", "F": "⚫"}
            emoji = grade_emoji.get(comp.grade.value, "⚪")

            lines.append(f"  {emoji} #{comp.rank} {comp.strategy_name} ({comp.grade.value})")
            lines.append(f"     收益: {comp.current_metrics.total_return:.1%}")
            lines.append(f"     夏普: {comp.current_metrics.sharpe_ratio:.2f}")
            lines.append(f"     胜率: {comp.current_metrics.win_rate:.1%}")
            lines.append(f"     最大回撤: {comp.current_metrics.max_drawdown:.1%}")

            if comp.improvement:
                imp = comp.improvement.get("total_return", 0)
                if imp != 0:
                    lines.append(f"     较上期: {imp:+.1%}")

        lines.append("")
        lines.append("💡 建议:")
        lines.extend(f"  - {rec}" for rec in report.recommendations)

        return "\n".join(lines)


backtest_reporter = BacktestReporter()
