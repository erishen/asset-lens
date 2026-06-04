import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    initial_capital: float = 100000.0
    position_size: float = 0.1
    max_position: float = 0.6
    single_stock_max: float = 0.2
    stop_loss: float = -0.08
    take_profit: float = 0.20
    signal_threshold: float = 0.6
    commission_rate: float = 0.0003
    slippage: float = 0.001


@dataclass
class BacktestTradeRecord:
    code: str
    name: str
    action: str
    date: str
    price: float
    shares: int
    amount: float
    commission: float
    signal_prob: float
    pnl: float = 0.0


@dataclass
class MLBacktestResult:
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    win_trades: int
    loss_trades: int
    avg_profit: float
    avg_loss: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    final_capital: float
    trades: list[dict[str, Any]] = field(default_factory=list)
    daily_returns: list[float] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_return": round(self.total_return, 4),
            "annual_return": round(self.annual_return, 4),
            "max_drawdown": round(self.max_drawdown, 4),
            "sharpe_ratio": round(self.sharpe_ratio, 4),
            "win_rate": round(self.win_rate, 4),
            "profit_factor": round(self.profit_factor, 4),
            "total_trades": self.total_trades,
            "win_trades": self.win_trades,
            "loss_trades": self.loss_trades,
            "avg_profit": round(self.avg_profit, 4),
            "avg_loss": round(self.avg_loss, 4),
            "max_consecutive_wins": self.max_consecutive_wins,
            "max_consecutive_losses": self.max_consecutive_losses,
            "final_capital": round(self.final_capital, 2),
            "trades_count": len(self.trades),
            "timestamp": self.timestamp,
        }


class BacktestExecutionMixin:
    def _execute_buy(
        self,
        code: str,
        price: float,
        date: str,
        amount: float,
        signal_prob: float,
    ) -> None:
        actual_price = price * (1 + self.config.slippage)
        commission = amount * self.config.commission_rate
        actual_amount = amount - commission
        shares = int(actual_amount / actual_price / 100) * 100

        if shares < 100:
            return

        actual_cost = shares * actual_price + commission

        if code in self.positions:
            old_position = self.positions[code]
            total_shares = old_position["shares"] + shares
            total_cost = old_position["cost"] + actual_cost
            self.positions[code] = {
                "shares": total_shares,
                "avg_price": total_cost / total_shares,
                "cost": total_cost,
                "value": total_shares * price,
            }
        else:
            self.positions[code] = {
                "shares": shares,
                "avg_price": actual_price,
                "cost": actual_cost,
                "value": shares * price,
            }

        self.capital -= actual_cost

        self.trades.append(
            BacktestTradeRecord(
                code=code,
                name="",
                action="buy",
                date=date,
                price=actual_price,
                shares=shares,
                amount=actual_cost,
                commission=commission,
                signal_prob=signal_prob,
            )
        )

    def _execute_sell(
        self,
        code: str,
        price: float,
        date: str,
        reason: str,
        signal_prob: float,
    ) -> None:
        if code not in self.positions:
            return

        position = self.positions[code]

        actual_price = price * (1 - self.config.slippage)
        sell_amount = position["shares"] * actual_price
        commission = sell_amount * self.config.commission_rate
        actual_amount = sell_amount - commission

        pnl = actual_amount - position["cost"]

        self.capital += actual_amount

        self.trades.append(
            BacktestTradeRecord(
                code=code,
                name="",
                action="sell",
                date=date,
                price=actual_price,
                shares=position["shares"],
                amount=actual_amount,
                commission=commission,
                signal_prob=signal_prob,
                pnl=pnl,
            )
        )

        del self.positions[code]

    def _update_equity_curve(
        self,
        price_data: dict[str, pd.DataFrame],
        date: str,
    ) -> None:
        position_value = 0.0

        for code, position in self.positions.items():
            df = price_data.get(code)
            if df is None or df.empty:
                continue

            day_data = df[df["date"] == date] if "date" in df.columns else df[df.index == date]

            if not day_data.empty:
                current_price = float(day_data["close"].iloc[0])
                position_value += position["shares"] * current_price

        total_equity = self.capital + position_value
        self.equity_curve.append(total_equity)

    def _close_all_positions(
        self,
        price_data: dict[str, pd.DataFrame],
        date: str | None,
    ) -> None:
        for code in list(self.positions.keys()):
            df = price_data.get(code)

            if df is None or df.empty:
                continue

            if date:
                day_data = df[df["date"] == date] if "date" in df.columns else df[df.index == date]
                last_price = float(day_data["close"].iloc[0]) if not day_data.empty else float(df["close"].iloc[-1])
            else:
                last_price = float(df["close"].iloc[-1])

            self._execute_sell(code, last_price, str(date or "end"), "close", 0.5)
