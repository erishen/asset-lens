from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TradeSignal:
    code: str
    name: str
    action: str
    confidence: float
    price: float
    reason: str
    market_condition: str
    strategy: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class AITradeRecord:
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
