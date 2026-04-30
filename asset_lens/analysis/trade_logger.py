"""
Enhanced Trading Log Module.
交易日志增强模块 - 记录更完整

功能:
1. 详细交易记录
2. 交易上下文记录
3. 决策依据记录
4. 执行结果追踪
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..config import config


class TradeAction(Enum):
    """交易动作"""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    WATCH = "watch"


class TradeSource(Enum):
    """交易来源"""

    MANUAL = "manual"
    AUTO = "auto"
    SIGNAL = "signal"
    ML = "ml"
    AI = "ai"


class TradeResult(Enum):
    """交易结果"""

    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    CANCELLED = "cancelled"


@dataclass
class TradeContext:
    """交易上下文"""

    market_trend: str
    market_change: float
    sentiment: str
    volatility: float
    index_name: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "market_trend": self.market_trend,
            "market_change": self.market_change,
            "sentiment": self.sentiment,
            "volatility": self.volatility,
            "index_name": self.index_name,
            "timestamp": self.timestamp,
        }


@dataclass
class DecisionBasis:
    """决策依据"""

    strategy_name: str
    strategy_score: float
    ml_prediction: float | None
    ml_direction: str | None
    ai_confidence: float | None
    ai_action: str | None
    signals: list[str]
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "strategy_score": self.strategy_score,
            "ml_prediction": self.ml_prediction,
            "ml_direction": self.ml_direction,
            "ai_confidence": self.ai_confidence,
            "ai_action": self.ai_action,
            "signals": self.signals,
            "reasons": self.reasons,
        }


@dataclass
class EnhancedTradeLog:
    """增强交易日志"""

    id: str
    code: str
    name: str
    action: TradeAction
    source: TradeSource
    result: TradeResult
    price: float
    shares: int
    amount: float
    context: TradeContext
    decision: DecisionBasis
    execution_time: float
    notes: str
    tags: list[str]
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "action": self.action.value,
            "source": self.source.value,
            "result": self.result.value,
            "price": self.price,
            "shares": self.shares,
            "amount": self.amount,
            "context": self.context.to_dict(),
            "decision": self.decision.to_dict(),
            "execution_time": self.execution_time,
            "notes": self.notes,
            "tags": self.tags,
            "created_at": self.created_at,
        }


@dataclass
class TradeStatistics:
    """交易统计"""

    total_trades: int
    buy_count: int
    sell_count: int
    success_count: int
    failed_count: int
    total_amount: float
    avg_execution_time: float
    by_source: dict[str, int]
    by_result: dict[str, int]


class EnhancedTradeLogger:
    """增强交易日志器"""

    LOG_FILE = "enhanced_trade_log.json"

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.log_file = self.cache_path / self.LOG_FILE

    def log_trade(
        self,
        code: str,
        name: str,
        action: TradeAction,
        source: TradeSource,
        result: TradeResult,
        price: float,
        shares: int,
        context: TradeContext,
        decision: DecisionBasis,
        execution_time: float = 0,
        notes: str = "",
        tags: list[str] | None = None,
    ) -> EnhancedTradeLog:
        """记录交易"""
        log_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{code}"

        log = EnhancedTradeLog(
            id=log_id,
            code=code,
            name=name,
            action=action,
            source=source,
            result=result,
            price=price,
            shares=shares,
            amount=price * shares,
            context=context,
            decision=decision,
            execution_time=execution_time,
            notes=notes,
            tags=tags or [],
        )

        self._save_log(log)

        return log

    def log_buy(
        self,
        code: str,
        name: str,
        price: float,
        shares: int,
        source: TradeSource = TradeSource.AUTO,
        context: TradeContext | None = None,
        decision: DecisionBasis | None = None,
        notes: str = "",
    ) -> EnhancedTradeLog:
        """记录买入"""
        if context is None:
            context = TradeContext(
                market_trend="未知",
                market_change=0,
                sentiment="中性",
                volatility=0,
                index_name="上证指数",
            )

        if decision is None:
            decision = DecisionBasis(
                strategy_name="default",
                strategy_score=0,
                ml_prediction=None,
                ml_direction=None,
                ai_confidence=None,
                ai_action=None,
                signals=[],
                reasons=[],
            )

        return self.log_trade(
            code=code,
            name=name,
            action=TradeAction.BUY,
            source=source,
            result=TradeResult.SUCCESS,
            price=price,
            shares=shares,
            context=context,
            decision=decision,
            notes=notes,
        )

    def log_sell(
        self,
        code: str,
        name: str,
        price: float,
        shares: int,
        source: TradeSource = TradeSource.AUTO,
        context: TradeContext | None = None,
        decision: DecisionBasis | None = None,
        notes: str = "",
    ) -> EnhancedTradeLog:
        """记录卖出"""
        if context is None:
            context = TradeContext(
                market_trend="未知",
                market_change=0,
                sentiment="中性",
                volatility=0,
                index_name="上证指数",
            )

        if decision is None:
            decision = DecisionBasis(
                strategy_name="default",
                strategy_score=0,
                ml_prediction=None,
                ml_direction=None,
                ai_confidence=None,
                ai_action=None,
                signals=[],
                reasons=[],
            )

        return self.log_trade(
            code=code,
            name=name,
            action=TradeAction.SELL,
            source=source,
            result=TradeResult.SUCCESS,
            price=price,
            shares=shares,
            context=context,
            decision=decision,
            notes=notes,
        )

    def get_statistics(self, days: int = 30) -> TradeStatistics:
        """获取交易统计"""
        logs = self._load_logs()

        cutoff = datetime.now()
        from datetime import timedelta

        cutoff = cutoff - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")

        recent = [l for l in logs if l["created_at"] >= cutoff_str]

        total = len(recent)
        buy_count = sum(1 for l in recent if l["action"] == "buy")
        sell_count = sum(1 for l in recent if l["action"] == "sell")
        success_count = sum(1 for l in recent if l["result"] == "success")
        failed_count = sum(1 for l in recent if l["result"] == "failed")

        total_amount = sum(l["amount"] for l in recent)
        avg_time = sum(l["execution_time"] for l in recent) / total if total > 0 else 0

        by_source: dict[str, int] = {}
        by_result: dict[str, int] = {}

        for l in recent:
            src = l["source"]
            by_source[src] = by_source.get(src, 0) + 1
            rlt = l["result"]
            by_result[rlt] = by_result.get(rlt, 0) + 1

        return TradeStatistics(
            total_trades=total,
            buy_count=buy_count,
            sell_count=sell_count,
            success_count=success_count,
            failed_count=failed_count,
            total_amount=total_amount,
            avg_execution_time=avg_time,
            by_source=by_source,
            by_result=by_result,
        )

    def get_recent_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        """获取最近日志"""
        logs = self._load_logs()
        return logs[-limit:]

    def search_logs(
        self,
        code: str | None = None,
        action: TradeAction | None = None,
        source: TradeSource | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        """搜索日志"""
        logs = self._load_logs()

        results: list[dict[str, Any]] = []
        for log in logs:
            if code and log["code"] != code:
                continue
            if action and log["action"] != action.value:
                continue
            if source and log["source"] != source.value:
                continue
            if start_date and log["created_at"] < start_date:
                continue
            if end_date and log["created_at"] > end_date:
                continue
            results.append(log)

        return results

    def _save_log(self, log: EnhancedTradeLog) -> None:
        """保存日志"""
        logs = self._load_logs()
        logs.append(log.to_dict())

        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(logs[-1000:], f, ensure_ascii=False, indent=2)

    def _load_logs(self) -> list[dict[str, Any]]:
        """加载日志"""
        if not self.log_file.exists():
            return []
        try:
            with open(self.log_file, encoding="utf-8") as f:
                data: list[dict[str, Any]] = json.load(f)
                return data
        except Exception:
            return []

    def format_statistics_report(self, stats: TradeStatistics) -> str:
        """格式化统计报告"""
        lines = [
            "\n📊 交易日志统计报告",
            "=" * 60,
            f"总交易数: {stats.total_trades}",
            f"买入: {stats.buy_count} | 卖出: {stats.sell_count}",
            f"成功: {stats.success_count} | 失败: {stats.failed_count}",
            f"总金额: ¥{stats.total_amount:,.2f}",
            f"平均执行时间: {stats.avg_execution_time:.2f}s",
            "",
            "📋 按来源统计:",
        ]

        for src, count in stats.by_source.items():
            lines.append(f"  {src}: {count}")

        lines.append("")
        lines.append("📋 按结果统计:")
        for rlt, count in stats.by_result.items():
            lines.append(f"  {rlt}: {count}")

        return "\n".join(lines)


enhanced_trade_logger = EnhancedTradeLogger()
