import logging
from typing import Any

logger = logging.getLogger(__name__)


class AITraderExecutionMixin:
    def execute_signals(self, signals) -> list:
        from datetime import datetime

        from .ai_trader_models import AITradeRecord

        logger.info("第四步: 执行交易...")

        trades = []
        holding_count = len([p for p in self.stock_pool.positions.values() if p.status == "holding"])

        buy_signals = [s for s in signals if s.action == "buy"]
        sell_signals = [s for s in signals if s.action == "sell"]

        for signal in sell_signals[:5]:
            if signal.code in self.stock_pool.positions:
                sell_pos = self.stock_pool.positions[signal.code]
                if sell_pos.status == "holding":
                    success, _ = self.stock_pool.sell_stock(signal.code, signal.price)
                    if success:
                        profit_rate = (signal.price - sell_pos.buy_price) / sell_pos.buy_price * 100
                        trade = AITradeRecord(
                            code=signal.code,
                            name=signal.name,
                            action="sell",
                            price=signal.price,
                            shares=sell_pos.shares,
                            amount=signal.price * sell_pos.shares,
                            confidence=signal.confidence,
                            market_condition=signal.market_condition,
                            strategy=signal.strategy,
                            reason=signal.reason,
                            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            profit_rate=profit_rate,
                        )
                        trades.append(trade)
                        self.trades.append(
                            {
                                "code": trade.code,
                                "name": trade.name,
                                "action": trade.action,
                                "price": trade.price,
                                "shares": trade.shares,
                                "amount": trade.amount,
                                "confidence": trade.confidence,
                                "market_condition": trade.market_condition,
                                "strategy": trade.strategy,
                                "reason": trade.reason,
                                "timestamp": trade.timestamp,
                                "profit_rate": trade.profit_rate,
                            }
                        )
                        logger.info(f"卖出 {signal.code} {signal.name} @ {signal.price:.2f} (收益: {profit_rate:+.2f}%)")

        for signal in buy_signals:
            if holding_count >= self.max_positions:
                break

            if signal.code not in self.stock_pool.positions:
                self.stock_pool.add_stock(
                    signal.code,
                    signal.name,
                    signal.price,
                    "watching",
                    signal.reason,
                )

            pos = self.stock_pool.positions.get(signal.code)
            if pos and pos.status != "holding":
                position_amount = self.current_capital * self.position_ratio
                shares = int(position_amount / signal.price / 100) * 100

                if shares >= 100:
                    success, _ = self.stock_pool.buy_stock(signal.code, signal.price, shares)
                    if success:
                        cost = signal.price * shares
                        self.current_capital -= cost
                        self._save_state()
                        trade = AITradeRecord(
                            code=signal.code,
                            name=signal.name,
                            action="buy",
                            price=signal.price,
                            shares=shares,
                            amount=signal.price * shares,
                            confidence=signal.confidence,
                            market_condition=signal.market_condition,
                            strategy=signal.strategy,
                            reason=signal.reason,
                            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        )
                        trades.append(trade)
                        self.trades.append(
                            {
                                "code": trade.code,
                                "name": trade.name,
                                "action": trade.action,
                                "price": trade.price,
                                "shares": trade.shares,
                                "amount": trade.amount,
                                "confidence": trade.confidence,
                                "market_condition": trade.market_condition,
                                "strategy": trade.strategy,
                                "reason": trade.reason,
                                "timestamp": trade.timestamp,
                            }
                        )
                        holding_count += 1
                        logger.info(f"买入 {signal.code} {signal.name} @ {signal.price:.2f} x {shares}股")

        self._save_trades()

        return trades

    def get_portfolio_summary(self) -> dict[str, Any]:
        holding_stocks = []
        total_market_value = 0.0
        total_profit = 0.0
        total_cost = 0.0

        for code, pos in self.stock_pool.positions.items():
            if pos.status == "holding":
                market_value = pos.current_price * pos.shares
                cost = pos.buy_price * pos.shares
                profit = (pos.current_price - pos.buy_price) * pos.shares
                profit_rate = (pos.current_price - pos.buy_price) / pos.buy_price * 100

                holding_stocks.append(
                    {
                        "code": code,
                        "name": pos.name,
                        "buy_price": pos.buy_price,
                        "current_price": pos.current_price,
                        "shares": pos.shares,
                        "market_value": market_value,
                        "profit": profit,
                        "profit_rate": profit_rate,
                    }
                )

                total_market_value += market_value
                total_profit += profit
                total_cost += cost

        total_value = self.current_capital + total_market_value
        total_profit_rate = (total_value - self.initial_capital) / self.initial_capital * 100

        return {
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "total_market_value": total_market_value,
            "total_cost": total_cost,
            "total_value": total_value,
            "total_profit": total_profit,
            "total_profit_rate": total_profit_rate,
            "holding_count": len(holding_stocks),
            "holdings": holding_stocks,
        }

    def show_trading_history(self, days: int = 7) -> None:
        from datetime import datetime, timedelta

        logger.info(f"交易历史 (最近{days}天)")
        logger.info("=" * 60)

        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        recent_trades = [t for t in self.trades if t.get("timestamp", "") >= cutoff]

        if not recent_trades:
            logger.info("  暂无交易记录")
            return

        for trade in recent_trades[-20:]:
            action_icon = "🟢" if trade["action"] == "buy" else "🔴"
            profit_str = ""
            if trade.get("profit_rate") is not None:
                profit_str = f" (收益: {trade['profit_rate']:+.2f}%)"

            logger.info(f"  {action_icon} {trade['timestamp']} {trade['code']} {trade['name']}")
            logger.info(f"     {trade['action'].upper()} @ ¥{trade['price']:.2f} x {trade['shares']}股{profit_str}")
            logger.info(f"     原因: {trade['reason']}")
