from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TradeType(Enum):
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    BONUS = "bonus"


class ReviewTradeResult(Enum):
    PROFIT = "profit"
    LOSS = "loss"
    BREAK_EVEN = "break_even"


@dataclass
class ReviewTradeRecord:
    code: str
    name: str
    trade_type: TradeType
    shares: float
    price: float
    amount: float
    commission: float
    timestamp: str
    reason: str = ""
    strategy: str = ""
    notes: str = ""


@dataclass
class ClosedPosition:
    code: str
    name: str
    buy_price: float
    sell_price: float
    shares: float
    profit_loss: float
    profit_loss_percent: float
    hold_days: int
    buy_date: str
    sell_date: str
    strategy: str = ""
    result: ReviewTradeResult = ReviewTradeResult.PROFIT


@dataclass
class PerformanceMetrics:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit: float
    total_loss: float
    net_profit: float
    avg_profit: float
    avg_loss: float
    profit_factor: float
    avg_hold_days: float
    max_profit_trade: float
    max_loss_trade: float
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0


@dataclass
class AttributionAnalysis:
    sector_contribution: dict[str, float]
    strategy_contribution: dict[str, float]
    time_contribution: dict[str, float]
    top_winners: list[ClosedPosition]
    top_losers: list[ClosedPosition]


@dataclass
class ReviewReport:
    period_start: str
    period_end: str
    report_type: str
    performance: PerformanceMetrics
    attribution: AttributionAnalysis
    trades: list[dict[str, Any]]
    closed_positions: list[ClosedPosition]
    suggestions: list[str]
    lessons_learned: list[str]
    next_period_plan: list[str]
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
