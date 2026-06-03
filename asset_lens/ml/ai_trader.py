import logging
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import config
from ..utils.json_cache import read_json_cache, write_json_cache
from ..trading.stock_pool import StockPool
from .ai_trader_execution import AITraderExecutionMixin
from .ai_trader_models import AITradeRecord, TradeSignal

logger = logging.getLogger(__name__)


class AISimulatedTrader(AITraderExecutionMixin):
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
        self.position_ratio = 0.2
        self.min_confidence = 0.55
        self.max_positions = 10

        self._load_history()
        self._load_state()

    def _load_history(self) -> None:
        signals = read_json_cache(self.signals_file)
        if signals:
            self.signals = signals

        trades = read_json_cache(self.trades_file)
        if trades:
            self.trades = trades

    def _load_state(self) -> None:
        state = read_json_cache(self.state_file)
        if state:
            self.current_capital = state.get("current_capital", self.initial_capital)

    def _save_state(self) -> None:
        from datetime import datetime

        state = {
            "current_capital": self.current_capital,
            "initial_capital": self.initial_capital,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        write_json_cache(self.state_file, state)

    def _save_signals(self) -> None:
        write_json_cache(self.signals_file, self.signals[-100:])

    def _save_trades(self) -> None:
        write_json_cache(self.trades_file, self.trades)

    def analyze_and_generate_signals(self) -> list[TradeSignal]:
        from .adaptive_trainer import AdaptiveStrategyConfig, AIMarketAnalyzer

        logger.info("=" * 60)
        logger.info("  AI模拟交易系统")
        logger.info("=" * 60)

        logger.info("第一步: AI分析市场...")
        analyzer = AIMarketAnalyzer()
        analysis = analyzer.analyze_market()

        self.market_condition = analysis.condition.value
        self.current_strategy = analysis.suggested_strategy

        console_print(f"  市场状态: {self.market_condition.upper()}")
        console_print(f"  风险等级: {analysis.risk_level}")
        console_print(f"  建议策略: {self.current_strategy}")

        strategy_config = AdaptiveStrategyConfig.get_config(analysis.condition)

        logger.info("第二步: 筛选候选股票...")
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

        logger.info(f"生成 {len(signals)} 个交易信号")

        return signals

    def _get_candidate_stocks(self, config: dict) -> list[dict[str, Any]]:
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

                except (ValueError, KeyError, RuntimeError) as e:
                    logger.debug(f"预测 {code} 失败: {e}")
                    continue

        except (ValueError, KeyError, RuntimeError, ConnectionError) as e:
            logger.warning(f"ML预测失败，使用规则策略: {e}")

        if not signals:
            logger.warning("ML未生成信号，使用规则策略补充")
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
                            code=code, name=name, action="buy",
                            confidence=0.6 + min(change / 20, 0.3), price=price,
                            reason=f"牛市动量策略: 涨幅{change:.1f}%, 换手{turnover:.1f}%",
                            market_condition=self.market_condition, strategy=self.current_strategy,
                        )
                    )

            elif self.market_condition == "bear":
                if change < -3 and turnover < 3:
                    signals.append(
                        TradeSignal(
                            code=code, name=name, action="sell",
                            confidence=0.6 + min(abs(change) / 20, 0.3), price=price,
                            reason=f"熊市防御策略: 跌幅{change:.1f}%",
                            market_condition=self.market_condition, strategy=self.current_strategy,
                        )
                    )

            elif self.market_condition == "volatile":
                if change < -5:
                    signals.append(
                        TradeSignal(
                            code=code, name=name, action="buy", confidence=0.65, price=price,
                            reason=f"反转策略: 超跌反弹机会 (跌幅{change:.1f}%)",
                            market_condition=self.market_condition, strategy=self.current_strategy,
                        )
                    )
                elif change < -3:
                    signals.append(
                        TradeSignal(
                            code=code, name=name, action="buy", confidence=0.58, price=price,
                            reason=f"反转策略: 跌幅较大可能有反弹 (跌幅{change:.1f}%)",
                            market_condition=self.market_condition, strategy=self.current_strategy,
                        )
                    )

            elif self.market_condition == "sideways" and -2 < change < 2 and turnover > 2:
                signals.append(
                    TradeSignal(
                        code=code, name=name, action="buy", confidence=0.55, price=price,
                        reason="震荡市策略: 横盘整理后可能突破",
                        market_condition=self.market_condition, strategy=self.current_strategy,
                    )
                )

        return signals[:10]

    def run_trading_session(self) -> dict[str, Any]:
        signals = self.analyze_and_generate_signals()
        trades = self.execute_signals(signals)

        summary = self.get_portfolio_summary()

        logger.info("交易会话总结:")
        logger.info(f"  市场状态: {self.market_condition.upper()}")
        logger.info(f"  使用策略: {self.current_strategy}")
        logger.info(f"  生成信号: {len(signals)} 个")
        logger.info(f"  执行交易: {len(trades)} 笔")
        logger.info(f"  当前持仓: {summary['holding_count']} 只")
        logger.info(f"  总资产: ¥{summary['total_value']:,.2f}")
        logger.info(f"  总收益: {summary['total_profit_rate']:+.2f}%")

        return {
            "market_condition": self.market_condition,
            "strategy": self.current_strategy,
            "signals_count": len(signals),
            "trades_count": len(trades),
            "trades": trades,
            "portfolio": summary,
        }


ai_trader = AISimulatedTrader()
