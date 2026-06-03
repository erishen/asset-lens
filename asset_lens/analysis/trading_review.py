"""
Trading Review Module.
复盘总结模块 - 交易记录和策略评估

功能:
1. 交易记录自动记录
2. 策略效果评估
3. 盈亏归因分析
4. 改进建议生成
5. 周报/月报自动生成
"""

from datetime import datetime, timedelta
from pathlib import Path

from ..utils.json_cache import read_json_cache, write_json_cache
from typing import Any

from ..config import config
from .review_models import (
    AttributionAnalysis,
    ClosedPosition,
    PerformanceMetrics,
    ReviewReport,
    ReviewTradeRecord,
    ReviewTradeResult,
    TradeType,
)

__all__ = [
    "AttributionAnalysis",
    "ClosedPosition",
    "PerformanceMetrics",
    "ReviewReport",
    "ReviewTradeRecord",
    "ReviewTradeResult",
    "TradeType",
    "TradingReview",
    "trading_review",
]


class TradingReview:
    """复盘总结器"""

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.trades_file = self.cache_path / "trades.json"
        self.closed_positions_file = self.cache_path / "closed_positions.json"
        self.reports_file = self.cache_path / "review_reports.json"

    def record_trade(
        self,
        code: str,
        name: str,
        trade_type: TradeType,
        shares: float,
        price: float,
        commission: float = 0.0,
        reason: str = "",
        strategy: str = "",
        notes: str = "",
    ) -> ReviewTradeRecord:
        """记录交易"""
        record = ReviewTradeRecord(
            code=code,
            name=name,
            trade_type=trade_type,
            shares=shares,
            price=price,
            amount=shares * price,
            commission=commission,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            reason=reason,
            strategy=strategy,
            notes=notes,
        )

        self._save_trade(record)
        return record

    def record_closed_position(
        self,
        code: str,
        name: str,
        buy_price: float,
        sell_price: float,
        shares: float,
        buy_date: str,
        sell_date: str,
        strategy: str = "",
    ) -> ClosedPosition:
        """记录平仓"""
        profit_loss = (sell_price - buy_price) * shares
        profit_loss_percent = (sell_price - buy_price) / buy_price * 100

        buy_dt = datetime.strptime(buy_date, "%Y-%m-%d")
        sell_dt = datetime.strptime(sell_date, "%Y-%m-%d")
        hold_days = (sell_dt - buy_dt).days

        result = (
            ReviewTradeResult.PROFIT
            if profit_loss > 0
            else (ReviewTradeResult.LOSS if profit_loss < 0 else ReviewTradeResult.BREAK_EVEN)
        )

        position = ClosedPosition(
            code=code,
            name=name,
            buy_price=buy_price,
            sell_price=sell_price,
            shares=shares,
            profit_loss=profit_loss,
            profit_loss_percent=profit_loss_percent,
            hold_days=hold_days,
            buy_date=buy_date,
            sell_date=sell_date,
            strategy=strategy,
            result=result,
        )

        self._save_closed_position(position)
        return position

    def calculate_performance(
        self,
        positions: list[ClosedPosition],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> PerformanceMetrics:
        """计算绩效指标"""
        if not positions:
            return PerformanceMetrics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_profit=0.0,
                total_loss=0.0,
                net_profit=0.0,
                avg_profit=0.0,
                avg_loss=0.0,
                profit_factor=0.0,
                avg_hold_days=0.0,
                max_profit_trade=0.0,
                max_loss_trade=0.0,
            )

        filtered = positions
        if start_date:
            filtered = [p for p in filtered if p.sell_date >= start_date]
        if end_date:
            filtered = [p for p in filtered if p.sell_date <= end_date]

        winning = [p for p in filtered if p.result == ReviewTradeResult.PROFIT]
        losing = [p for p in filtered if p.result == ReviewTradeResult.LOSS]

        total_profit = sum(p.profit_loss for p in winning)
        total_loss = abs(sum(p.profit_loss for p in losing))
        net_profit = total_profit - total_loss

        avg_profit = total_profit / len(winning) if winning else 0.0
        avg_loss = total_loss / len(losing) if losing else 0.0

        profit_factor = total_profit / total_loss if total_loss > 0 else float("inf") if total_profit > 0 else 0.0

        avg_hold = sum(p.hold_days for p in filtered) / len(filtered) if filtered else 0.0

        max_profit = max((p.profit_loss for p in filtered), default=0.0)
        max_loss = min((p.profit_loss for p in filtered), default=0.0)

        return PerformanceMetrics(
            total_trades=len(filtered),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate=len(winning) / len(filtered) * 100 if filtered else 0.0,
            total_profit=total_profit,
            total_loss=total_loss,
            net_profit=net_profit,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            avg_hold_days=avg_hold,
            max_profit_trade=max_profit,
            max_loss_trade=max_loss,
        )

    def analyze_attribution(
        self,
        positions: list[ClosedPosition],
    ) -> AttributionAnalysis:
        """归因分析"""
        sector_contribution: dict[str, float] = {}
        strategy_contribution: dict[str, float] = {}
        time_contribution: dict[str, float] = {}

        for p in positions:
            sector = "未知"
            if sector not in sector_contribution:
                sector_contribution[sector] = 0.0
            sector_contribution[sector] += p.profit_loss

            strategy = p.strategy or "未分类"
            if strategy not in strategy_contribution:
                strategy_contribution[strategy] = 0.0
            strategy_contribution[strategy] += p.profit_loss

            month = p.sell_date[:7]
            if month not in time_contribution:
                time_contribution[month] = 0.0
            time_contribution[month] += p.profit_loss

        sorted_by_profit = sorted(positions, key=lambda p: p.profit_loss, reverse=True)
        top_winners = sorted_by_profit[:5]
        top_losers = sorted_by_profit[-5:][::-1]

        return AttributionAnalysis(
            sector_contribution=sector_contribution,
            strategy_contribution=strategy_contribution,
            time_contribution=time_contribution,
            top_winners=top_winners,
            top_losers=top_losers,
        )

    def generate_suggestions(
        self,
        performance: PerformanceMetrics,
        attribution: AttributionAnalysis,
    ) -> list[str]:
        """生成改进建议"""
        suggestions = []

        if performance.win_rate < 50:
            suggestions.append("胜率低于 50%，建议优化选股策略或提高信号质量")
        elif performance.win_rate < 60:
            suggestions.append("胜率一般，可进一步优化入场时机")

        if performance.profit_factor < 1.5:
            suggestions.append("盈亏比偏低，建议优化止盈止损策略")
        elif performance.profit_factor > 3:
            suggestions.append("盈亏比优秀，保持当前策略")

        if performance.avg_hold_days > 30:
            suggestions.append("平均持仓时间较长，可考虑缩短持仓周期")
        elif performance.avg_hold_days < 3:
            suggestions.append("平均持仓时间较短，可能错过大趋势")

        if abs(performance.max_loss_trade) > performance.avg_profit * 3:
            suggestions.append("最大亏损过大，建议加强风险控制")

        if attribution.top_losers:
            suggestions.extend(f"避免在类似 {p.code} 的情况下交易" for p in attribution.top_losers)

        if not suggestions:
            suggestions.append("策略表现良好，继续保持")

        return suggestions

    def generate_lessons_learned(
        self,
        positions: list[ClosedPosition],
    ) -> list[str]:
        """生成经验教训"""
        lessons = []

        big_winners = [p for p in positions if p.profit_loss_percent > 20]
        if big_winners:
            lessons.append(
                f"大盈利案例: {big_winners[0].code} 盈利 {big_winners[0].profit_loss_percent:.1f}%，持仓 {big_winners[0].hold_days} 天"
            )

        big_losers = [p for p in positions if p.profit_loss_percent < -10]
        if big_losers:
            lessons.append(
                f"大亏损教训: {big_losers[0].code} 亏损 {abs(big_losers[0].profit_loss_percent):.1f}%，需加强止损"
            )

        quick_trades = [p for p in positions if p.hold_days <= 3 and p.result == ReviewTradeResult.LOSS]
        if len(quick_trades) > len(positions) * 0.3:
            lessons.append("短线交易亏损较多，建议减少频繁交易")

        return lessons

    def generate_report(
        self,
        report_type: str = "weekly",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> ReviewReport:
        """生成复盘报告"""
        positions = self._load_closed_positions()

        if not start_date:
            today = datetime.now()
            if report_type == "daily":
                start_date = today.strftime("%Y-%m-%d")
            elif report_type == "weekly":
                start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            else:
                start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")

        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        performance = self.calculate_performance(positions, start_date, end_date)
        attribution = self.analyze_attribution(positions)
        suggestions = self.generate_suggestions(performance, attribution)
        lessons = self.generate_lessons_learned(positions)

        trades = self._load_trades()

        next_plan = [
            "继续执行当前策略",
            "关注市场变化",
            "严格执行止损纪律",
        ]

        report = ReviewReport(
            period_start=start_date,
            period_end=end_date,
            report_type=report_type,
            performance=performance,
            attribution=attribution,
            trades=trades,
            closed_positions=positions,
            suggestions=suggestions,
            lessons_learned=lessons,
            next_period_plan=next_plan,
        )

        self._save_report(report)
        return report

    def format_report(self, report: ReviewReport) -> str:
        """格式化报告"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"📊 {report.report_type.upper()} 复盘报告")
        lines.append(f"   期间: {report.period_start} ~ {report.period_end}")
        lines.append("=" * 60)
        lines.append("")

        p = report.performance
        lines.append("📈 绩效概览:")
        lines.append(f"   总交易次数: {p.total_trades}")
        lines.append(f"   盈利次数: {p.winning_trades} | 亏损次数: {p.losing_trades}")
        lines.append(f"   胜率: {p.win_rate:.1f}%")
        lines.append(f"   总盈利: {p.total_profit:.2f} | 总亏损: {p.total_loss:.2f}")
        lines.append(f"   净利润: {p.net_profit:.2f}")
        lines.append(f"   盈亏比: {p.profit_factor:.2f}")
        lines.append(f"   平均持仓: {p.avg_hold_days:.1f} 天")
        lines.append("")

        if report.attribution.top_winners:
            lines.append("🏆 盈利 TOP 3:")
            lines.extend(
                f"   {pos.code} {pos.name}: +{pos.profit_loss_percent:.1f}%"
                for pos in report.attribution.top_winners[:3]
            )
            lines.append("")

        if report.attribution.top_losers:
            lines.append("📉 亏损 TOP 3:")
            lines.extend(
                f"   {pos.code} {pos.name}: {pos.profit_loss_percent:.1f}%" for pos in report.attribution.top_losers[:3]
            )
            lines.append("")

        lines.append("💡 改进建议:")
        lines.extend(f"   • {s}" for s in report.suggestions)
        lines.append("")

        lines.append("📝 经验教训:")
        lines.extend(f"   • {l}" for l in report.lessons_learned)
        lines.append("")

        lines.append("📋 下期计划:")
        lines.extend(f"   • {plan}" for plan in report.next_period_plan)
        lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def _save_trade(self, record: ReviewTradeRecord) -> None:
        """保存交易记录"""
        trades = self._load_trades()
        trades.append(
            {
                "code": record.code,
                "name": record.name,
                "type": record.trade_type.value,
                "shares": record.shares,
                "price": record.price,
                "amount": record.amount,
                "commission": record.commission,
                "timestamp": record.timestamp,
                "reason": record.reason,
                "strategy": record.strategy,
            }
        )

        write_json_cache(self.trades_file, trades)

    def _load_trades(self) -> list[dict[str, Any]]:
        """加载交易记录"""
        data = read_json_cache(self.trades_file)
        return data if data else []

    def _save_closed_position(self, position: ClosedPosition) -> None:
        """保存平仓记录"""
        positions_data = self._load_closed_positions_data()
        positions_data.append(
            {
                "code": position.code,
                "name": position.name,
                "buy_price": position.buy_price,
                "sell_price": position.sell_price,
                "shares": position.shares,
                "profit_loss": position.profit_loss,
                "profit_loss_percent": position.profit_loss_percent,
                "hold_days": position.hold_days,
                "buy_date": position.buy_date,
                "sell_date": position.sell_date,
                "strategy": position.strategy,
                "result": position.result.value,
            }
        )

        write_json_cache(self.closed_positions_file, positions_data)

    def _load_closed_positions(self) -> list[ClosedPosition]:
        """加载平仓记录"""
        data = self._load_closed_positions_data()
        positions: list[ClosedPosition] = [
            ClosedPosition(
                code=item["code"],
                name=item["name"],
                buy_price=item["buy_price"],
                sell_price=item["sell_price"],
                shares=item["shares"],
                profit_loss=item["profit_loss"],
                profit_loss_percent=item["profit_loss_percent"],
                hold_days=item["hold_days"],
                buy_date=item["buy_date"],
                sell_date=item["sell_date"],
                strategy=item.get("strategy", ""),
                result=ReviewTradeResult(item.get("result", "profit")),
            )
            for item in data
        ]

        return positions

    def _load_closed_positions_data(self) -> list[dict[str, Any]]:
        """加载平仓记录原始数据"""
        data = read_json_cache(self.closed_positions_file)
        return data if data else []

    def _save_report(self, report: ReviewReport) -> None:
        """保存报告"""
        reports = []
        reports_data = read_json_cache(self.reports_file)
        if reports_data:
            reports = reports_data

        reports.append(
            {
                "period_start": report.period_start,
                "period_end": report.period_end,
                "type": report.report_type,
                "performance": {
                    "total_trades": report.performance.total_trades,
                    "win_rate": report.performance.win_rate,
                    "net_profit": report.performance.net_profit,
                },
                "timestamp": report.timestamp,
            }
        )

        if len(reports) > 100:
            reports = reports[-100:]

        write_json_cache(self.reports_file, reports)


trading_review = TradingReview()
