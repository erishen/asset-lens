from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from .simulator_models import (
    RebalanceFrequency,
    SimulatedPosition,
    SimulatedTrade,
    SimulationConfig,
    SimulationResult,
)


class StrategySimulator:
    def __init__(self, config: SimulationConfig | None = None):
        self.config = config or SimulationConfig()
        self.positions: dict[str, SimulatedPosition] = {}
        self.trades: list[SimulatedTrade] = []
        self.daily_values: list[dict[str, Any]] = []
        self.cash: float = self.config.initial_capital
        self.last_rebalance_date: str | None = None

    def should_rebalance(self, current_date: str) -> bool:
        if self.last_rebalance_date is None:
            return True

        last = datetime.strptime(self.last_rebalance_date, "%Y-%m-%d")
        current = datetime.strptime(current_date, "%Y-%m-%d")
        delta = (current - last).days

        freq = self.config.rebalance_frequency
        if freq == RebalanceFrequency.DAILY:
            return delta >= 1
        elif freq == RebalanceFrequency.WEEKLY:
            return delta >= 7
        elif freq == RebalanceFrequency.BIWEEKLY:
            return delta >= 14
        elif freq == RebalanceFrequency.MONTHLY:
            return delta >= 30
        elif freq == RebalanceFrequency.QUARTERLY:
            return delta >= 90

        return False

    def calculate_position_weight(self, score: float, total_score: float) -> float:
        if total_score <= 0:
            return self.config.min_position_weight

        base_weight = score / total_score
        weighted = base_weight * self.config.max_position_weight * 2

        return max(self.config.min_position_weight, min(weighted, self.config.max_position_weight))

    def execute_buy(
        self,
        code: str,
        name: str,
        price: float,
        weight: float,
        date: str,
        reason: str = "rebalance",
    ) -> SimulatedTrade | None:
        if code in self.positions:
            return None

        if price <= 0:
            return None

        target_value = self.cash * weight
        shares = int(target_value / price / 100) * 100

        if shares < 100:
            return None

        amount = shares * price
        commission = amount * self.config.commission_rate
        slippage = amount * self.config.slippage_rate
        total_cost = amount + commission + slippage

        if total_cost > self.cash:
            shares = (
                int((self.cash / (1 + self.config.commission_rate + self.config.slippage_rate)) / price / 100) * 100
            )
            if shares < 100:
                return None
            amount = shares * price
            commission = amount * self.config.commission_rate
            slippage = amount * self.config.slippage_rate
            total_cost = amount + commission + slippage

        self.cash -= total_cost

        position = SimulatedPosition(
            code=code,
            name=name,
            entry_date=date,
            entry_price=price,
            shares=shares,
            weight=weight,
            current_price=price,
            current_value=amount,
            highest_price=price,
            stop_loss_price=price * (1 - self.config.stop_loss_pct),
            take_profit_price=price * (1 + self.config.take_profit_pct),
            stop_loss_type=self.config.stop_loss_type,
            stop_loss_pct=self.config.stop_loss_pct,
        )
        self.positions[code] = position

        trade = SimulatedTrade(
            date=date,
            code=code,
            name=name,
            action="buy",
            price=price,
            shares=shares,
            amount=amount,
            commission=commission,
            slippage=slippage,
            reason=reason,
        )
        self.trades.append(trade)

        return trade

    def execute_sell(
        self,
        code: str,
        price: float,
        date: str,
        reason: str = "rebalance",
    ) -> SimulatedTrade | None:
        if code not in self.positions:
            return None

        position = self.positions[code]

        amount = position.shares * price
        commission = amount * self.config.commission_rate
        slippage = amount * self.config.slippage_rate
        net_amount = amount - commission - slippage

        profit = net_amount - (position.entry_price * position.shares)
        profit_rate = profit / (position.entry_price * position.shares)

        self.cash += net_amount

        trade = SimulatedTrade(
            date=date,
            code=code,
            name=position.name,
            action="sell",
            price=price,
            shares=position.shares,
            amount=amount,
            commission=commission,
            slippage=slippage,
            reason=reason,
            profit=profit,
            profit_rate=profit_rate,
        )
        self.trades.append(trade)

        del self.positions[code]

        return trade

    def check_stop_loss_take_profit(self, date: str, prices: dict[str, float]) -> list[SimulatedTrade]:
        trades: list[SimulatedTrade] = []

        for code, position in list(self.positions.items()):
            price = prices.get(code, position.current_price)
            position.update_price(price)

            if position.should_stop_loss():
                trade = self.execute_sell(code, price, date, "stop_loss")
                if trade:
                    trades.append(trade)
            elif position.should_take_profit():
                trade = self.execute_sell(code, price, date, "take_profit")
                if trade:
                    trades.append(trade)

        return trades

    def check_holding_period(self, date: str) -> list[str]:
        to_sell: list[str] = []
        current = datetime.strptime(date, "%Y-%m-%d")

        for code, position in self.positions.items():
            entry = datetime.strptime(position.entry_date, "%Y-%m-%d")
            holding_days = (current - entry).days
            position.holding_days = holding_days

            if holding_days >= self.config.max_holding_days:
                to_sell.append(code)

        return to_sell

    def can_sell_position(self, code: str, date: str, reason: str = "rebalance") -> bool:
        if code not in self.positions:
            return False

        position = self.positions[code]

        if reason in ("stop_loss", "take_profit", "max_holding"):
            return True

        entry = datetime.strptime(position.entry_date, "%Y-%m-%d")
        current = datetime.strptime(date, "%Y-%m-%d")
        holding_days = (current - entry).days

        return holding_days >= self.config.min_holding_days

    def get_total_value(self, prices: dict[str, float]) -> float:
        positions_value = sum(prices.get(code, pos.current_price) * pos.shares for code, pos in self.positions.items())
        return self.cash + positions_value

    def run_simulation(
        self,
        stock_pool_data: list[dict[str, Any]],
        price_history: dict[str, list[dict[str, Any]]],
        start_date: str,
        end_date: str,
        selection_func: Callable | None = None,
        benchmark_prices: dict[str, float] | None = None,
    ) -> SimulationResult:
        self.positions = {}
        self.trades = []
        self.daily_values = []
        self.cash = self.config.initial_capital
        self.last_rebalance_date = None

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")

            prices: dict[str, float] = {}
            for code, history in price_history.items():
                for item in history:
                    if item.get("date") == date_str:
                        prices[code] = item.get("price", item.get("close", 0))
                        break

            self.check_stop_loss_take_profit(date_str, prices)

            to_sell = self.check_holding_period(date_str)
            for code in to_sell:
                if code in prices:
                    self.execute_sell(code, prices[code], date_str, "max_holding")

            if self.should_rebalance(date_str):
                if selection_func:
                    selected = selection_func(stock_pool_data, date_str)
                else:
                    selected = sorted(stock_pool_data, key=lambda x: x.get("score", 0), reverse=True)
                    selected = selected[: self.config.max_positions]

                for code in list(self.positions.keys()):
                    if (
                        code not in [s.get("code") for s in selected]
                        and code in prices
                        and self.can_sell_position(code, date_str, "rebalance")
                    ):
                        self.execute_sell(code, prices[code], date_str, "rebalance")

                total_score = sum(s.get("score", 0) for s in selected)

                for stock in selected:
                    code = stock.get("code", "")
                    if code not in self.positions and code in prices:
                        weight = self.calculate_position_weight(stock.get("score", 0), total_score)
                        self.execute_buy(
                            code=code,
                            name=stock.get("name", ""),
                            price=prices[code],
                            weight=weight,
                            date=date_str,
                            reason="rebalance",
                        )

                self.last_rebalance_date = date_str

            total_value = self.get_total_value(prices)
            self.daily_values.append(
                {
                    "date": date_str,
                    "total_value": total_value,
                    "cash": self.cash,
                    "positions_value": total_value - self.cash,
                    "positions_count": len(self.positions),
                }
            )

            current += timedelta(days=1)

        return self._calculate_result(start_date, end_date, benchmark_prices)

    def _calculate_result(
        self,
        start_date: str,
        end_date: str,
        benchmark_prices: dict[str, float] | None = None,
    ) -> SimulationResult:
        final_capital = self.daily_values[-1]["total_value"] if self.daily_values else self.config.initial_capital
        total_return = (final_capital - self.config.initial_capital) / self.config.initial_capital * 100

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days
        annual_return = total_return * 365 / days if days > 0 else 0

        max_value = self.config.initial_capital
        max_drawdown = 0.0
        for dv in self.daily_values:
            if dv["total_value"] > max_value:
                max_value = dv["total_value"]
            drawdown = (max_value - dv["total_value"]) / max_value * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        win_trades = [t for t in self.trades if t.action == "sell" and t.profit > 0]
        lose_trades = [t for t in self.trades if t.action == "sell" and t.profit <= 0]
        total_sell_trades = len(win_trades) + len(lose_trades)
        win_rate = len(win_trades) / total_sell_trades * 100 if total_sell_trades > 0 else 0

        total_commission = sum(t.commission for t in self.trades)
        total_slippage = sum(t.slippage for t in self.trades)

        total_buy_amount = sum(t.amount for t in self.trades if t.action == "buy")
        turnover_rate = total_buy_amount / self.config.initial_capital * 100

        returns = []
        for i in range(1, len(self.daily_values)):
            prev = self.daily_values[i - 1]["total_value"]
            curr = self.daily_values[i]["total_value"]
            if prev > 0:
                returns.append((curr - prev) / prev)

        sharpe_ratio = 0.0
        if returns:
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            std_return = variance**0.5
            if std_return > 0:
                sharpe_ratio = avg_return / std_return * (252**0.5)

        benchmark_return = 0.0
        excess_return = total_return

        if benchmark_prices:
            benchmark_start = benchmark_prices.get(start_date)
            benchmark_end = benchmark_prices.get(end_date)
            if benchmark_start and benchmark_end:
                benchmark_return = (benchmark_end - benchmark_start) / benchmark_start * 100
                excess_return = total_return - benchmark_return

        return SimulationResult(
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.config.initial_capital,
            final_capital=round(final_capital, 2),
            total_return=round(total_return, 2),
            annual_return=round(annual_return, 2),
            benchmark_return=round(benchmark_return, 4),
            excess_return=round(excess_return, 4),
            max_drawdown=round(max_drawdown, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            win_rate=round(win_rate, 2),
            total_trades=len(self.trades),
            win_trades=len(win_trades),
            lose_trades=len(lose_trades),
            turnover_rate=round(turnover_rate, 2),
            total_commission=round(total_commission, 2),
            total_slippage=round(total_slippage, 2),
            trades=self.trades,
            daily_values=self.daily_values,
            positions=list(self.positions.values()),
        )


strategy_simulator = StrategySimulator()


__all__ = [
    "RebalanceFrequency",
    "SimulatedPosition",
    "SimulatedTrade",
    "SimulationConfig",
    "SimulationResult",
    "StrategySimulator",
    "strategy_simulator",
]
