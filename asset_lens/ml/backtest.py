import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .backtest_execution import (
    BacktestConfig,
    BacktestExecutionMixin,
    BacktestTradeRecord,
    MLBacktestResult,
)

logger = logging.getLogger(__name__)


class BacktestEngine(BacktestExecutionMixin):
    def __init__(self, config: BacktestConfig | None = None):
        self.config = config or BacktestConfig()
        self.trades: list[BacktestTradeRecord] = []
        self.positions: dict[str, dict[str, Any]] = {}
        self.capital = self.config.initial_capital
        self.equity_curve: list[float] = []

    def run_backtest(
        self,
        predictions: pd.DataFrame,
        price_data: dict[str, pd.DataFrame],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> MLBacktestResult:
        self._reset()

        if start_date:
            predictions = predictions[predictions["date"] >= start_date]
        if end_date:
            predictions = predictions[predictions["date"] <= end_date]

        predictions = predictions.sort_values("date")

        all_dates = sorted(predictions["date"].unique())

        for date in all_dates:
            day_preds = predictions[predictions["date"] == date]

            self._process_sell_signals(day_preds, price_data, date)
            self._process_buy_signals(day_preds, price_data, date)

            self._update_equity_curve(price_data, date)

        self._close_all_positions(price_data, all_dates[-1] if all_dates else None)

        return self._calculate_result()

    def _reset(self) -> None:
        self.trades = []
        self.positions = {}
        self.capital = self.config.initial_capital
        self.equity_curve = []

    def _process_sell_signals(
        self,
        predictions: pd.DataFrame,
        price_data: dict[str, pd.DataFrame],
        date: str,
    ) -> None:
        for _, row in predictions.iterrows():
            code = row["code"]

            if code not in self.positions:
                continue

            position = self.positions[code]
            df = price_data.get(code)

            if df is None or df.empty:
                continue

            day_data = df[df["date"] == date] if "date" in df.columns else df[df.index == date]

            if day_data.empty:
                continue

            current_price = float(day_data["close"].iloc[0])
            buy_price = position["avg_price"]
            pnl_pct = (current_price - buy_price) / buy_price

            should_sell = False
            sell_reason = ""

            if pnl_pct <= self.config.stop_loss:
                should_sell = True
                sell_reason = "stop_loss"
            elif pnl_pct >= self.config.take_profit:
                should_sell = True
                sell_reason = "take_profit"
            elif row.get("prediction", 0) == 0 and row.get("up_prob", 0) < 0.4:
                should_sell = True
                sell_reason = "signal"

            if should_sell:
                self._execute_sell(code, current_price, date, sell_reason, row.get("up_prob", 0))

    def _process_buy_signals(
        self,
        predictions: pd.DataFrame,
        price_data: dict[str, pd.DataFrame],
        date: str,
    ) -> None:
        for _, row in predictions.iterrows():
            code = row["code"]

            if row.get("prediction", 0) != 1:
                continue

            up_prob = row.get("up_prob", 0)
            if up_prob < self.config.signal_threshold:
                continue

            total_position = sum(p["value"] for p in self.positions.values())
            total_position_pct = total_position / self.capital

            if total_position_pct >= self.config.max_position:
                continue

            if code in self.positions:
                current_pct = self.positions[code]["value"] / self.capital
                if current_pct >= self.config.single_stock_max:
                    continue

            df = price_data.get(code)
            if df is None or df.empty:
                continue

            day_data = df[df["date"] == date] if "date" in df.columns else df[df.index == date]

            if day_data.empty:
                continue

            current_price = float(day_data["close"].iloc[0])

            position_multiplier = min(1.5, 1.0 + (up_prob - 0.6) * 2)
            position_size = self.config.position_size * position_multiplier
            position_size = min(position_size, self.config.single_stock_max)

            available_capital = self.capital * (self.config.max_position - total_position_pct)
            buy_amount = min(self.capital * position_size, available_capital)

            if buy_amount < 1000:
                continue

            self._execute_buy(code, current_price, date, buy_amount, up_prob)

    def _calculate_result(self) -> MLBacktestResult:
        if not self.equity_curve:
            return MLBacktestResult(
                total_return=0.0,
                annual_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                total_trades=0,
                win_trades=0,
                loss_trades=0,
                avg_profit=0.0,
                avg_loss=0.0,
                max_consecutive_wins=0,
                max_consecutive_losses=0,
                final_capital=self.config.initial_capital,
            )

        final_capital = self.equity_curve[-1]
        total_return = (final_capital / self.config.initial_capital - 1) * 100

        trading_days = len(self.equity_curve)
        annual_return = ((final_capital / self.config.initial_capital) ** (252 / max(trading_days, 1)) - 1) * 100

        equity_series = pd.Series(self.equity_curve)
        rolling_max = equity_series.cummax()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100

        daily_returns = equity_series.pct_change().dropna()
        sharpe_ratio = 0.0
        if len(daily_returns) > 1 and daily_returns.std() > 0:
            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)

        sell_trades = [t for t in self.trades if t.action == "sell"]
        total_trades = len(sell_trades)

        if total_trades == 0:
            return MLBacktestResult(
                total_return=total_return,
                annual_return=annual_return,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                win_rate=0.0,
                profit_factor=0.0,
                total_trades=0,
                win_trades=0,
                loss_trades=0,
                avg_profit=0.0,
                avg_loss=0.0,
                max_consecutive_wins=0,
                max_consecutive_losses=0,
                final_capital=final_capital,
            )

        profits = [t.pnl for t in sell_trades if t.pnl > 0]
        losses = [t.pnl for t in sell_trades if t.pnl < 0]

        win_trades = len(profits)
        loss_trades = len(losses)
        win_rate = win_trades / total_trades * 100 if total_trades > 0 else 0

        avg_profit = float(np.mean(profits)) if profits else 0.0
        avg_loss = float(np.mean(losses)) if losses else 0.0

        total_profit = sum(profits) if profits else 0
        total_loss = abs(sum(losses)) if losses else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else 0

        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0

        for t in sell_trades:
            if t.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)

        return MLBacktestResult(
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            win_trades=win_trades,
            loss_trades=loss_trades,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            max_consecutive_wins=max_consecutive_wins,
            max_consecutive_losses=max_consecutive_losses,
            final_capital=final_capital,
            trades=[
                {
                    "code": t.code,
                    "action": t.action,
                    "date": t.date,
                    "price": t.price,
                    "shares": t.shares,
                    "pnl": t.pnl,
                }
                for t in self.trades
            ],
            daily_returns=list(daily_returns),
            equity_curve=self.equity_curve,
        )


class SignalValidator:
    def __init__(self, prediction_days: int = 5):
        self.prediction_days = prediction_days

    def validate_signals(
        self,
        predictions: pd.DataFrame,
        price_data: dict[str, pd.DataFrame],
    ) -> dict[str, Any]:
        results: dict[str, Any] = {
            "total_signals": 0,
            "correct_signals": 0,
            "accuracy": 0.0,
            "avg_return": 0.0,
            "win_rate": 0.0,
            "avg_hold_days": 0.0,
            "by_confidence": {},
        }

        by_confidence: dict[str, dict[str, Any]] = results["by_confidence"]

        signal_returns = []
        correct_count = 0
        total_signals = 0

        for _, row in predictions.iterrows():
            code = row["code"]
            date = row["date"]
            prediction = row.get("prediction", 0)
            up_prob = row.get("up_prob", 0)

            if prediction != 1:
                continue

            total_signals += 1

            df = price_data.get(code)
            if df is None or df.empty:
                continue

            if "date" in df.columns:
                df = df.sort_values("date")
                signal_idx = df[df["date"] == date].index
                if len(signal_idx) == 0:
                    continue
                signal_idx = signal_idx[0]

                future_idx = signal_idx + self.prediction_days
                if future_idx >= len(df):
                    continue

                current_price = df.loc[signal_idx, "close"]
                future_price = df.loc[future_idx, "close"]
            else:
                continue

            actual_return = (future_price - current_price) / current_price
            signal_returns.append(actual_return)

            if actual_return > 0:
                correct_count += 1

            conf_bucket = f"{int(up_prob * 10) * 10}-{int(up_prob * 10) * 10 + 10}%"
            if conf_bucket not in by_confidence:
                by_confidence[conf_bucket] = {"count": 0, "correct": 0, "returns": []}
            by_confidence[conf_bucket]["count"] += 1
            if actual_return > 0:
                by_confidence[conf_bucket]["correct"] += 1
            by_confidence[conf_bucket]["returns"].append(actual_return)

        results["total_signals"] = total_signals
        results["correct_signals"] = correct_count
        results["accuracy"] = correct_count / total_signals * 100 if total_signals > 0 else 0
        results["avg_return"] = np.mean(signal_returns) * 100 if signal_returns else 0
        results["win_rate"] = (
            sum(1 for r in signal_returns if r > 0) / len(signal_returns) * 100 if signal_returns else 0
        )

        for bucket in by_confidence:
            data = by_confidence[bucket]
            data["accuracy"] = data["correct"] / data["count"] * 100 if data["count"] > 0 else 0
            data["avg_return"] = np.mean(data["returns"]) * 100 if data["returns"] else 0

        return results


def generate_backtest_report(
    result: MLBacktestResult,
    signal_validation: dict[str, Any] | None = None,
    output_path: Path | None = None,
) -> str:
    report_lines = [
        "=" * 60,
        "                    回测报告",
        "=" * 60,
        "",
        "【收益指标】",
        f"  总收益率:     {result.total_return:.2f}%",
        f"  年化收益率:   {result.annual_return:.2f}%",
        f"  最大回撤:     {result.max_drawdown:.2f}%",
        f"  夏普比率:     {result.sharpe_ratio:.2f}",
        "",
        "【交易统计】",
        f"  总交易次数:   {result.total_trades}",
        f"  盈利次数:     {result.win_trades}",
        f"  亏损次数:     {result.loss_trades}",
        f"  胜率:         {result.win_rate:.2f}%",
        f"  盈亏比:       {result.profit_factor:.2f}",
        "",
        "【盈亏分析】",
        f"  平均盈利:     {result.avg_profit:.2f}",
        f"  平均亏损:     {result.avg_loss:.2f}",
        f"  最大连续盈利: {result.max_consecutive_wins} 次",
        f"  最大连续亏损: {result.max_consecutive_losses} 次",
        "",
        "【资金情况】",
        "  初始资金:     100,000.00",
        f"  最终资金:     {result.final_capital:.2f}",
        "",
    ]

    if signal_validation:
        report_lines.extend(
            [
                "【信号验证】",
                f"  总信号数:     {signal_validation['total_signals']}",
                f"  正确信号:     {signal_validation['correct_signals']}",
                f"  信号准确率:   {signal_validation['accuracy']:.2f}%",
                f"  平均收益:     {signal_validation['avg_return']:.2f}%",
                f"  信号胜率:     {signal_validation['win_rate']:.2f}%",
                "",
            ]
        )

        if signal_validation.get("by_confidence"):
            report_lines.append("  【按置信度分布】")
            for bucket, data in sorted(signal_validation["by_confidence"].items()):
                report_lines.append(
                    f"    {bucket}: {data['count']}次, 准确率{data['accuracy']:.1f}%, 平均收益{data['avg_return']:.2f}%"
                )
            report_lines.append("")

    report_lines.extend(
        [
            "=" * 60,
            f"报告生成时间: {result.timestamp}",
            "=" * 60,
        ]
    )

    report = "\n".join(report_lines)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"回测报告已保存: {output_path}")

    return report


backtest_engine = BacktestEngine()
signal_validator = SignalValidator()
