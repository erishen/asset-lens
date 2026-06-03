from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class HealthLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class TrendDirection(Enum):
    STRONG_UP = "strong_up"
    UP = "up"
    SIDEWAYS = "sideways"
    DOWN = "down"
    STRONG_DOWN = "strong_down"


@dataclass
class Position:
    code: str
    name: str
    shares: float
    cost_price: float
    current_price: float
    market_value: float
    profit_loss: float
    profit_loss_percent: float
    weight: float
    industry: str = ""
    sector: str = ""


@dataclass
class StockDiagnosis:
    code: str
    name: str
    current_price: float
    trend: TrendDirection
    health_score: float
    health_level: HealthLevel

    technical_score: float = 0.0
    fundamental_score: float = 0.0
    sentiment_score: float = 0.0

    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    support_levels: list[float] = field(default_factory=list)
    resistance_levels: list[float] = field(default_factory=list)

    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class PortfolioHealth:
    total_value: float
    total_profit_loss: float
    total_profit_loss_percent: float

    health_score: float
    health_level: HealthLevel

    diversification_score: float
    concentration_risk: float
    sector_balance: float

    top_positions: list[Position]
    risk_positions: list[Position]

    suggestions: list[str] = field(default_factory=list)


@dataclass
class SectorAllocation:
    sector: str
    weight: float
    profit_loss: float
    profit_loss_percent: float
    positions: list[Position]
