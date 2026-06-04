from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RebalanceFrequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class StopLossType(Enum):
    FIXED = "fixed"
    TRAILING = "trailing"
    ATR_BASED = "atr_based"


@dataclass
class SimulationConfig:
    initial_capital: float = 1000000.0
    max_positions: int = 10
    max_position_weight: float = 0.15
    min_position_weight: float = 0.05
    rebalance_frequency: RebalanceFrequency = RebalanceFrequency.WEEKLY
    stop_loss_pct: float = 0.08
    take_profit_pct: float = 0.20
    stop_loss_type: StopLossType = StopLossType.FIXED
    min_holding_days: int = 5
    max_holding_days: int = 60
    commission_rate: float = 0.0003
    slippage_rate: float = 0.001
    benchmark_code: str = "sh000300"


@dataclass
class SimulatedPosition:
    code: str
    name: str
    entry_date: str
    entry_price: float
    shares: int
    weight: float
    current_price: float = 0.0
    current_value: float = 0.0
    profit: float = 0.0
    profit_rate: float = 0.0
    holding_days: int = 0
    highest_price: float = 0.0
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    stop_loss_type: StopLossType = StopLossType.FIXED
    stop_loss_pct: float = 0.08
    _atr: float | None = None
    _atr_multiplier: float = 2.0

    def update_price(self, new_price: float) -> None:
        self.current_price = new_price
        self.current_value = new_price * self.shares
        self.profit = self.current_value - (self.entry_price * self.shares)
        self.profit_rate = (self.current_price - self.entry_price) / self.entry_price

        if new_price > self.highest_price:
            self.highest_price = new_price

        self._update_stop_loss_price(new_price)

    def _update_stop_loss_price(self, new_price: float) -> None:
        if self.stop_loss_type == StopLossType.TRAILING:
            if new_price > self.highest_price:
                trailing_price = self.highest_price * (1 - self.stop_loss_pct)
                self.stop_loss_price = trailing_price
        elif self.stop_loss_type == StopLossType.ATR_BASED:
            if self._atr is not None:
                self.stop_loss_price = new_price - self._atr * self._atr_multiplier
            else:
                self.stop_loss_price = self.entry_price * (1 - self.stop_loss_pct)
        else:
            self.stop_loss_price = self.entry_price * (1 - self.stop_loss_pct)

    def should_stop_loss(self) -> bool:
        if self.stop_loss_price <= 0:
            return False
        return self.current_price <= self.stop_loss_price

    def should_take_profit(self) -> bool:
        if self.take_profit_price <= 0:
            return False
        return self.current_price >= self.take_profit_price


@dataclass
class SimulatedTrade:
    date: str
    code: str
    name: str
    action: str
    price: float
    shares: int
    amount: float
    commission: float
    slippage: float
    reason: str
    profit: float = 0.0
    profit_rate: float = 0.0


@dataclass
class SimulationResult:
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return: float
    annual_return: float
    benchmark_return: float
    excess_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    win_trades: int
    lose_trades: int
    turnover_rate: float
    total_commission: float
    total_slippage: float
    trades: list[SimulatedTrade] = field(default_factory=list)
    daily_values: list[dict[str, Any]] = field(default_factory=list)
    positions: list[SimulatedPosition] = field(default_factory=list)
