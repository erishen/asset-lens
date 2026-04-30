"""
Backtesting system for asset-lens.
回测系统 - 策略历史表现验证

功能:
1. 历史数据回测
2. 绩效分析
3. 风险评估
4. 策略优化建议
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ..config import config

if TYPE_CHECKING:
    pass


@dataclass
class BacktestTrade:
    """回测交易记录"""

    date: str
    code: str
    name: str
    action: str  # buy, sell
    price: float
    shares: int
    amount: float
    profit: float = 0
    profit_rate: float = 0
    reason: str = ""


@dataclass
class BacktestResult:
    """回测结果"""

    strategy_name: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return: float
    annual_return: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    total_trades: int
    win_trades: int
    lose_trades: int
    avg_profit: float
    avg_loss: float
    trades: list[BacktestTrade] = field(default_factory=list)
    daily_values: list[dict[str, Any]] = field(default_factory=list)


class Backtester:
    """回测引擎"""

    def __init__(self):
        self.backtest_path = config.cache_path / "backtests"
        self.backtest_path.mkdir(parents=True, exist_ok=True)

    def _get_trading_dates(
        self,
        historical_data: dict[str, list[dict[str, Any]]],
        start_date: str | None,
        end_date: str | None,
    ) -> list[str]:
        """获取交易日列表"""
        all_dates_set = set()
        for _, data_list in historical_data.items():
            for data in data_list:
                all_dates_set.add(data.get("date", ""))

        all_dates: list[str] = sorted([d for d in all_dates_set if d])
        if not all_dates:
            raise ValueError("没有历史数据")

        if start_date:
            all_dates = [d for d in all_dates if d >= start_date]
        if end_date:
            all_dates = [d for d in all_dates if d <= end_date]

        if not all_dates:
            raise ValueError("日期范围内没有数据")

        return all_dates

    def _get_daily_stocks(
        self,
        historical_data: dict[str, list[dict[str, Any]]],
        date: str,
    ) -> list[dict[str, Any]]:
        """获取指定日期的所有股票数据"""
        daily_stocks = []
        for code, data_list in historical_data.items():
            for data in data_list:
                if data.get("date") == date:
                    daily_stocks.append({**data, "code": code})
                    break
        return daily_stocks

    def _update_position_values(
        self,
        positions: dict[str, dict[str, Any]],
        daily_stocks: list[dict[str, Any]],
    ) -> float:
        """更新持仓市值，返回总市值"""
        position_value = 0
        for code, pos in positions.items():
            for stock in daily_stocks:
                if stock.get("code") == code:
                    pos["current_price"] = stock.get("close", pos["buy_price"])
                    position_value += pos["current_price"] * pos["shares"]
                    break
        return position_value

    def _check_sell_conditions(
        self,
        pos: dict[str, Any],
        current_price: float,
        holding_days: int,
        strategy: Any,
    ) -> tuple[bool, str]:
        """检查卖出条件，返回 (是否卖出, 原因)"""
        profit_rate = (current_price - pos["buy_price"]) / pos["buy_price"]

        if profit_rate <= strategy.stop_loss:
            return True, f"止损 ({profit_rate * 100:.1f}%)"

        if profit_rate >= strategy.take_profit:
            return True, f"止盈 ({profit_rate * 100:.1f}%)"

        if holding_days >= strategy.holding_period_max:
            return True, f"持有到期 ({holding_days}天)"

        return False, ""

    def _execute_sell(
        self,
        code: str,
        pos: dict[str, Any],
        stock_data: dict[str, Any],
        date: str,
        sell_reason: str,
        slippage_rate: float,
        commission_rate: float,
        trades: list[BacktestTrade],
    ) -> float:
        """执行卖出，返回卖出金额"""
        current_price = stock_data.get("close", pos["buy_price"])
        sell_price = current_price * (1 - slippage_rate)
        amount = sell_price * pos["shares"]
        commission = amount * commission_rate
        profit = (sell_price - pos["buy_price"]) * pos["shares"] - commission
        profit_rate = (current_price - pos["buy_price"]) / pos["buy_price"]

        trades.append(
            BacktestTrade(
                date=date,
                code=code,
                name=stock_data.get("name", ""),
                action="sell",
                price=sell_price,
                shares=pos["shares"],
                amount=amount,
                profit=profit,
                profit_rate=profit_rate,
                reason=sell_reason,
            )
        )

        return float(amount - commission)

    def _find_buy_candidates(
        self,
        daily_stocks: list[dict[str, Any]],
        positions: dict[str, dict[str, Any]],
        strategy_name: str,
        strategy_engine: Any,
    ) -> list[dict[str, Any]]:
        """筛选符合条件的买入候选股票"""
        candidates = []
        for stock in daily_stocks:
            if stock.get("code") in positions:
                continue

            evaluation = strategy_engine.evaluate_stock(stock, strategy_name)
            if evaluation["match"] and evaluation["score"] >= 60:
                candidates.append(
                    {
                        **stock,
                        "strategy_score": evaluation["score"],
                    }
                )

        candidates.sort(key=lambda x: x.get("strategy_score", 0), reverse=True)
        return candidates

    def _execute_buy(
        self,
        candidate: dict[str, Any],
        date: str,
        capital: float,
        initial_capital: float,
        position_size: float,
        slippage_rate: float,
        commission_rate: float,
        trades: list[BacktestTrade],
    ) -> tuple[float, dict[str, Any] | None]:
        """执行买入，返回 (剩余资金, 持仓信息)"""
        buy_price = candidate.get("close", 0) * (1 + slippage_rate)
        position_amount = initial_capital * position_size
        shares = int(position_amount / buy_price / 100) * 100

        if shares < 100:
            return capital, None

        amount = buy_price * shares
        commission = amount * commission_rate

        if capital < amount + commission:
            return capital, None

        trades.append(
            BacktestTrade(
                date=date,
                code=candidate["code"],
                name=candidate.get("name", ""),
                action="buy",
                price=buy_price,
                shares=shares,
                amount=amount,
                reason=f"策略得分: {candidate.get('strategy_score', 0):.1f}",
            )
        )

        return capital - amount - commission, {
            "shares": shares,
            "buy_price": buy_price,
            "buy_date": date,
            "current_price": buy_price,
        }

    def _calculate_performance(
        self,
        daily_values: list[dict[str, Any]],
        trades: list[BacktestTrade],
        initial_capital: float,
        all_dates: list[str],
    ) -> dict[str, float | int]:
        """计算绩效指标"""
        final_capital = daily_values[-1]["total_value"] if daily_values else initial_capital
        total_return = (final_capital - initial_capital) / initial_capital

        days = len(all_dates)
        annual_return = (pow(final_capital / initial_capital, 365 / days) - 1) if days > 0 else 0

        max_value = initial_capital
        max_drawdown = 0
        for dv in daily_values:
            max_value = max(max_value, dv["total_value"])
            drawdown = (max_value - dv["total_value"]) / max_value
            max_drawdown = max(max_drawdown, drawdown)

        win_trades = [t for t in trades if t.action == "sell" and t.profit > 0]
        lose_trades = [t for t in trades if t.action == "sell" and t.profit <= 0]
        total_sell_trades = len(win_trades) + len(lose_trades)
        win_rate = len(win_trades) / total_sell_trades * 100 if total_sell_trades > 0 else 0

        avg_profit = sum(t.profit for t in win_trades) / len(win_trades) if win_trades else 0
        avg_loss = sum(t.profit for t in lose_trades) / len(lose_trades) if lose_trades else 0
        profit_factor = abs(avg_profit / avg_loss) if avg_loss != 0 else 0

        returns = []
        for i in range(1, len(daily_values)):
            daily_return = (daily_values[i]["total_value"] - daily_values[i - 1]["total_value"]) / daily_values[i - 1][
                "total_value"
            ]
            returns.append(daily_return)

        avg_return = sum(returns) / len(returns) if returns else 0
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns) if returns else 0
        std_return = variance**0.5
        sharpe_ratio = (avg_return * 252) / (std_return * (252**0.5)) if std_return > 0 else 0

        return {
            "final_capital": final_capital,
            "total_return": total_return,
            "annual_return": annual_return,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe_ratio,
            "win_trades": len(win_trades),
            "lose_trades": len(lose_trades),
            "avg_profit": avg_profit,
            "avg_loss": avg_loss,
        }

    def run_backtest(
        self,
        strategy_name: str,
        historical_data: dict[str, list[dict[str, Any]]],
        initial_capital: float = 100000,
        start_date: str | None = None,
        end_date: str | None = None,
        commission_rate: float = 0.0003,
        slippage_rate: float = 0.001,
    ) -> BacktestResult:
        """
        运行回测

        Args:
            strategy_name: 策略名称
            historical_data: 历史数据 {code: [daily_data]}
            initial_capital: 初始资金
            start_date: 开始日期
            end_date: 结束日期
            commission_rate: 手续费率
            slippage_rate: 滑点率

        Returns:
            回测结果
        """
        from .engine import strategy_engine

        strategy = strategy_engine.get_strategy(strategy_name)
        if not strategy:
            raise ValueError(f"策略 {strategy_name} 不存在")

        all_dates = self._get_trading_dates(historical_data, start_date, end_date)

        capital = initial_capital
        positions: dict[str, dict[str, Any]] = {}
        trades: list[BacktestTrade] = []
        daily_values: list[dict[str, Any]] = []

        for date in all_dates:
            daily_stocks = self._get_daily_stocks(historical_data, date)

            position_value = self._update_position_values(positions, daily_stocks)

            total_value = capital + position_value
            daily_values.append(
                {
                    "date": date,
                    "capital": capital,
                    "position_value": position_value,
                    "total_value": total_value,
                    "positions": len(positions),
                }
            )

            for code in list(positions.keys()):
                pos = positions[code]
                stock_data = next((s for s in daily_stocks if s.get("code") == code), None)

                if not stock_data:
                    continue

                current_price = stock_data.get("close", pos["buy_price"])
                holding_days = (
                    datetime.strptime(date, "%Y-%m-%d") - datetime.strptime(pos["buy_date"], "%Y-%m-%d")
                ).days

                should_sell, sell_reason = self._check_sell_conditions(pos, current_price, holding_days, strategy)

                if should_sell:
                    sell_capital = self._execute_sell(
                        code, pos, stock_data, date, sell_reason, slippage_rate, commission_rate, trades
                    )
                    capital += sell_capital
                    del positions[code]

            if len(positions) < strategy.max_positions:
                candidates = self._find_buy_candidates(daily_stocks, positions, strategy_name, strategy_engine)

                for candidate in candidates[: strategy.max_positions - len(positions)]:
                    if capital < initial_capital * strategy.position_size:
                        break

                    capital, new_pos = self._execute_buy(
                        candidate,
                        date,
                        capital,
                        initial_capital,
                        strategy.position_size,
                        slippage_rate,
                        commission_rate,
                        trades,
                    )

                    if new_pos:
                        positions[candidate["code"]] = new_pos

        perf = self._calculate_performance(daily_values, trades, initial_capital, all_dates)

        return BacktestResult(
            strategy_name=strategy_name,
            start_date=all_dates[0],
            end_date=all_dates[-1],
            initial_capital=initial_capital,
            final_capital=float(perf["final_capital"]),
            total_return=float(perf["total_return"]),
            annual_return=float(perf["annual_return"]),
            max_drawdown=float(perf["max_drawdown"]),
            win_rate=float(perf["win_rate"]),
            profit_factor=float(perf["profit_factor"]),
            sharpe_ratio=float(perf["sharpe_ratio"]),
            total_trades=len(trades),
            win_trades=int(perf["win_trades"]),
            lose_trades=int(perf["lose_trades"]),
            avg_profit=float(perf["avg_profit"]),
            avg_loss=float(perf["avg_loss"]),
            trades=trades,
            daily_values=daily_values,
        )

    def _save_backtest(self, result: BacktestResult) -> None:
        """保存回测结果"""
        filename = f"{result.strategy_name}_{result.start_date}_{result.end_date}.json"
        filepath = self.backtest_path / filename

        data = {
            "strategy_name": result.strategy_name,
            "start_date": result.start_date,
            "end_date": result.end_date,
            "initial_capital": result.initial_capital,
            "final_capital": result.final_capital,
            "total_return": result.total_return,
            "annual_return": result.annual_return,
            "max_drawdown": result.max_drawdown,
            "win_rate": result.win_rate,
            "profit_factor": result.profit_factor,
            "sharpe_ratio": result.sharpe_ratio,
            "total_trades": result.total_trades,
            "win_trades": result.win_trades,
            "lose_trades": result.lose_trades,
            "avg_profit": result.avg_profit,
            "avg_loss": result.avg_loss,
            "trades": [
                {
                    "date": t.date,
                    "code": t.code,
                    "name": t.name,
                    "action": t.action,
                    "price": t.price,
                    "shares": t.shares,
                    "amount": t.amount,
                    "profit": t.profit,
                    "profit_rate": t.profit_rate,
                    "reason": t.reason,
                }
                for t in result.trades
            ],
            "daily_values": result.daily_values,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def compare_strategies(
        self,
        strategies: list[str],
        historical_data: dict[str, list[dict[str, Any]]],
        **kwargs,
    ) -> dict[str, BacktestResult]:
        """
        比较多个策略

        Args:
            strategies: 策略名称列表
            historical_data: 历史数据
            **kwargs: 其他参数

        Returns:
            策略名称到回测结果的映射
        """
        results = {}
        for strategy_name in strategies:
            try:
                result = self.run_backtest(strategy_name, historical_data, **kwargs)
                results[strategy_name] = result
            except Exception as e:
                print(f"策略 {strategy_name} 回测失败: {e}")

        return results

    def get_best_strategy(
        self,
        strategies: list[str],
        historical_data: dict[str, list[dict[str, Any]]],
        metric: str = "sharpe_ratio",
        **kwargs,
    ) -> tuple[str, BacktestResult]:
        """
        获取最佳策略

        Args:
            strategies: 策略名称列表
            historical_data: 历史数据
            metric: 评估指标
            **kwargs: 其他参数

        Returns:
            (策略名称, 回测结果)
        """
        results = self.compare_strategies(strategies, historical_data, **kwargs)

        if not results:
            raise ValueError("所有策略回测失败")

        best_strategy = max(results.items(), key=lambda x: getattr(x[1], metric, 0))
        return best_strategy


backtester = Backtester()
