"""
AI-driven simulated trading system.
AI驱动的模拟交易系统

整合:
1. AI市场分析
2. ML预测模型
3. 自适应策略
4. 模拟交易执行
"""

# pylint: disable=no-value-for-parameter,no-member
# type: ignore[assignment]

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import config
from ..trading.stock_pool import StockPool, StockPosition

logger = logging.getLogger(__name__)


@dataclass
class TradeSignal:
    """交易信号"""

    code: str
    name: str
    action: str  # buy, sell, hold
    confidence: float
    price: float
    reason: str
    market_condition: str
    strategy: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class TradeRecord:
    """交易记录"""

    code: str
    name: str
    action: str
    price: float
    shares: int
    amount: float
    confidence: float
    market_condition: str
    strategy: str
    reason: str
    timestamp: str
    profit_rate: float | None = None


class AISimulatedTrader:
    """AI模拟交易员"""

    def __init__(self, pool_name: str = "ai_trading"):
        self.pool_name = pool_name
        self.stock_pool = StockPool(pool_name)
        self.trading_path = config.cache_path / "ai_trading"
        self.trading_path.mkdir(parents=True, exist_ok=True)

        self.signals_file = self.trading_path / "signals.json"
        self.trades_file = self.trading_path / "trades.json"
        self.state_file = self.trading_path / "state.json"
        self.signals: list[dict[str, Any]] = []
        self.trades: list[dict[str, Any]] = []

        self.market_condition = "sideways"
        self.current_strategy = "value"
        self.initial_capital = 100000.0
        self.current_capital = self.initial_capital
        self.position_ratio = 0.2  # 单只股票最大仓位比例
        self.min_confidence = 0.55  # 最小置信度阈值
        self.max_positions = 10  # 最大持仓数量

        self._load_history()
        self._load_state()

    def _load_history(self) -> None:
        """加载历史数据"""
        if self.signals_file.exists():
            with open(self.signals_file, encoding="utf-8") as f:
                self.signals = json.load(f)

        if self.trades_file.exists():
            with open(self.trades_file, encoding="utf-8") as f:
                self.trades = json.load(f)

    def _load_state(self) -> None:
        """加载交易状态"""
        if self.state_file.exists():
            with open(self.state_file, encoding="utf-8") as f:
                state = json.load(f)
                self.current_capital = state.get("current_capital", self.initial_capital)

    def _save_state(self) -> None:
        """保存交易状态"""
        state = {
            "current_capital": self.current_capital,
            "initial_capital": self.initial_capital,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def _save_signals(self) -> None:
        """保存信号"""
        with open(self.signals_file, "w", encoding="utf-8") as f:
            json.dump(self.signals[-100:], f, ensure_ascii=False, indent=2)

    def _save_trades(self) -> None:
        """保存交易记录"""
        with open(self.trades_file, "w", encoding="utf-8") as f:
            json.dump(self.trades, f, ensure_ascii=False, indent=2)

    def analyze_and_generate_signals(self) -> list[TradeSignal]:
        """
        分析市场并生成交易信号

        Returns:
            交易信号列表
        """
        from .adaptive_trainer import AdaptiveStrategyConfig, AIMarketAnalyzer

        console_print = print

        console_print("\n" + "=" * 60)
        console_print("  🤖 AI模拟交易系统")
        console_print("=" * 60)

        console_print("\n📊 第一步: AI分析市场...")
        analyzer = AIMarketAnalyzer()
        analysis = analyzer.analyze_market()

        self.market_condition = analysis.condition.value
        self.current_strategy = analysis.suggested_strategy

        console_print(f"  市场状态: {self.market_condition.upper()}")
        console_print(f"  风险等级: {analysis.risk_level}")
        console_print(f"  建议策略: {self.current_strategy}")

        strategy_config = AdaptiveStrategyConfig.get_config(analysis.condition)

        console_print("\n🎯 第二步: 筛选候选股票...")
        candidates = self._get_candidate_stocks(strategy_config)
        console_print(f"  候选股票: {len(candidates)} 只")

        console_print("\n🔮 第三步: ML预测生成信号...")
        signals = self._generate_signals(candidates, strategy_config, analysis)

        for signal in signals:
            self.signals.append(
                {
                    "code": signal.code,
                    "name": signal.name,
                    "action": signal.action,
                    "confidence": signal.confidence,
                    "price": signal.price,
                    "reason": signal.reason,
                    "market_condition": signal.market_condition,
                    "strategy": signal.strategy,
                    "timestamp": signal.timestamp,
                }
            )

        self._save_signals()

        console_print(f"\n✅ 生成 {len(signals)} 个交易信号")

        return signals

    def _get_candidate_stocks(self, config: dict) -> list[dict[str, Any]]:
        """获取候选股票"""
        from ..data.market_stock_fetcher import MarketStockFetcher

        fetcher = MarketStockFetcher()
        stocks = fetcher.get_cached_market_stocks()

        candidates = []
        for stock in stocks:
            code = stock.get("code", "")
            name = stock.get("name", "")
            if not code or not name:
                continue
            if "ST" in name or "*" in name:
                continue

            market_cap = stock.get("market_cap", 0)
            turnover = stock.get("turnover_rate", 0)
            price = stock.get("current_price", 0)

            if price <= 0:
                continue

            if (
                config["min_market_cap"] <= market_cap <= config["max_market_cap"]
                and config["min_turnover"] <= turnover <= config["max_turnover"]
            ):
                candidates.append(
                    {
                        "code": code,
                        "name": name,
                        "price": price,
                        "market_cap": market_cap,
                        "turnover": turnover,
                        "change_percent": stock.get("change_percent", 0),
                    }
                )

        return candidates[:100]

    def _generate_signals(
        self,
        candidates: list[dict],
        config: dict,
        analysis,
    ) -> list[TradeSignal]:
        """生成交易信号"""
        signals = []

        try:
            from .trainer import ModelTrainer

            trainer = ModelTrainer()
            model_path = Path("cache/ml/model_adaptive.pkl")

            if not model_path.exists():
                model_path = Path("cache/ml/model.pkl")

            if model_path.exists():
                trainer.load_model(model_path)

            from ..db.database import db_manager

            for candidate in candidates:
                code = candidate["code"]
                name = candidate["name"]
                price = candidate["price"]

                klines = db_manager.get_klines(code, limit=250)

                if len(klines) < 30:
                    continue

                df = pd.DataFrame(klines)
                df["date"] = pd.to_datetime(df["date"])
                df = df.sort_values("date").reset_index(drop=True)

                for col in ["open", "close", "high", "low", "volume", "amount"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

                try:
                    result = trainer.predictor.predict_stock(
                        df.to_dict("records")[0] if not df.empty else {}, code=code
                    )
                    prediction = result.prediction if hasattr(result, "prediction") else 0
                    confidence = result.confidence if hasattr(result, "confidence") else 0

                    if prediction == 1 and confidence >= self.min_confidence:
                        action = "buy"
                        reason = f"ML预测上涨 (置信度: {confidence:.1%})"
                        signals.append(
                            TradeSignal(
                                code=code,
                                name=name,
                                action=action,
                                confidence=confidence,
                                price=price,
                                reason=reason,
                                market_condition=self.market_condition,
                                strategy=self.current_strategy,
                            )
                        )

                except Exception as e:
                    logger.debug(f"预测 {code} 失败: {e}")
                    continue

        except Exception as e:
            print(f"  [yellow]ML预测失败，使用规则策略: {e}[/yellow]")

        if not signals:
            print("  [yellow]ML未生成信号，使用规则策略补充[/yellow]")
            rule_signals = self._rule_based_signals(candidates, config, analysis)
            signals.extend(rule_signals)

        signals.sort(key=lambda x: x.confidence, reverse=True)
        return signals[:20]

    def _rule_based_signals(
        self,
        candidates: list[dict],
        config: dict,
        analysis,
    ) -> list[TradeSignal]:
        """基于规则的信号生成"""
        signals = []

        for candidate in candidates:
            code = candidate["code"]
            name = candidate["name"]
            price = candidate["price"]
            change = candidate.get("change_percent", 0)
            turnover = candidate.get("turnover", 0)

            if self.market_condition == "bull":
                if change > 2 and turnover > 3:
                    signals.append(
                        TradeSignal(
                            code=code,
                            name=name,
                            action="buy",
                            confidence=0.6 + min(change / 20, 0.3),
                            price=price,
                            reason=f"牛市动量策略: 涨幅{change:.1f}%, 换手{turnover:.1f}%",
                            market_condition=self.market_condition,
                            strategy=self.current_strategy,
                        )
                    )

            elif self.market_condition == "bear":
                if change < -3 and turnover < 3:
                    signals.append(
                        TradeSignal(
                            code=code,
                            name=name,
                            action="sell",
                            confidence=0.6 + min(abs(change) / 20, 0.3),
                            price=price,
                            reason=f"熊市防御策略: 跌幅{change:.1f}%",
                            market_condition=self.market_condition,
                            strategy=self.current_strategy,
                        )
                    )

            elif self.market_condition == "volatile":
                if change < -5:
                    signals.append(
                        TradeSignal(
                            code=code,
                            name=name,
                            action="buy",
                            confidence=0.65,
                            price=price,
                            reason=f"反转策略: 超跌反弹机会 (跌幅{change:.1f}%)",
                            market_condition=self.market_condition,
                            strategy=self.current_strategy,
                        )
                    )
                elif change < -3:
                    signals.append(
                        TradeSignal(
                            code=code,
                            name=name,
                            action="buy",
                            confidence=0.58,
                            price=price,
                            reason=f"反转策略: 跌幅较大可能有反弹 (跌幅{change:.1f}%)",
                            market_condition=self.market_condition,
                            strategy=self.current_strategy,
                        )
                    )

            elif self.market_condition == "sideways" and -2 < change < 2 and turnover > 2:
                signals.append(
                    TradeSignal(
                        code=code,
                        name=name,
                        action="buy",
                        confidence=0.55,
                        price=price,
                        reason="震荡市策略: 横盘整理后可能突破",
                        market_condition=self.market_condition,
                        strategy=self.current_strategy,
                    )
                )

        return signals[:10]

    def execute_signals(self, signals: list[TradeSignal]) -> list[TradeRecord]:
        """
        执行交易信号

        Args:
            signals: 交易信号列表

        Returns:
            交易记录列表
        """
        print("\n💼 第四步: 执行交易...")

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
                        trade = TradeRecord(
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
                        print(f"  🔴 卖出 {signal.code} {signal.name} @ {signal.price:.2f} (收益: {profit_rate:+.2f}%)")

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

            pos: StockPosition | None = self.stock_pool.positions.get(signal.code)
            if pos and pos.status != "holding":
                position_amount = self.current_capital * self.position_ratio
                shares = int(position_amount / signal.price / 100) * 100

                if shares >= 100:
                    success, _ = self.stock_pool.buy_stock(signal.code, signal.price, shares)
                    if success:
                        cost = signal.price * shares
                        self.current_capital -= cost
                        self._save_state()
                        trade = TradeRecord(
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
                        print(f"  🟢 买入 {signal.code} {signal.name} @ {signal.price:.2f} x {shares}股")

        self._save_trades()

        return trades

    def run_trading_session(self) -> dict[str, Any]:
        """
        运行一次完整的交易会话

        Returns:
            交易会话结果
        """
        signals = self.analyze_and_generate_signals()
        trades = self.execute_signals(signals)

        summary = self.get_portfolio_summary()

        print("\n📊 交易会话总结:")
        print(f"  市场状态: {self.market_condition.upper()}")
        print(f"  使用策略: {self.current_strategy}")
        print(f"  生成信号: {len(signals)} 个")
        print(f"  执行交易: {len(trades)} 笔")
        print(f"  当前持仓: {summary['holding_count']} 只")
        print(f"  总资产: ¥{summary['total_value']:,.2f}")
        print(f"  总收益: {summary['total_profit_rate']:+.2f}%")

        return {
            "market_condition": self.market_condition,
            "strategy": self.current_strategy,
            "signals_count": len(signals),
            "trades_count": len(trades),
            "trades": trades,
            "portfolio": summary,
        }

    def get_portfolio_summary(self) -> dict[str, Any]:
        """获取投资组合摘要"""
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
        """显示交易历史"""
        from datetime import timedelta

        print(f"\n📜 交易历史 (最近{days}天)")
        print("=" * 60)

        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        recent_trades = [t for t in self.trades if t.get("timestamp", "") >= cutoff]

        if not recent_trades:
            print("  暂无交易记录")
            return

        for trade in recent_trades[-20:]:
            action_icon = "🟢" if trade["action"] == "buy" else "🔴"
            profit_str = ""
            if trade.get("profit_rate") is not None:
                profit_str = f" (收益: {trade['profit_rate']:+.2f}%)"

            print(f"  {action_icon} {trade['timestamp']} {trade['code']} {trade['name']}")
            print(f"     {trade['action'].upper()} @ ¥{trade['price']:.2f} x {trade['shares']}股{profit_str}")
            print(f"     原因: {trade['reason']}")


ai_trader = AISimulatedTrader()
