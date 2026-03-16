"""
Trading module - 交易相关功能
"""

from .auto_trader import AutoTrader, auto_trader
from .stock_pool import StockPool, StockPosition, stock_pool
from .risk_manager import RiskManager, risk_manager
from .stock_pool_builder import (
    StockPoolBuilder,
    StockEntryMatrix,
    EntryReason,
    FilterCondition,
    FactorCategory,
    stock_pool_builder,
)
from .strategy_simulator import (
    StrategySimulator,
    SimulationConfig,
    SimulationResult,
    SimulatedPosition,
    SimulatedTrade,
    RebalanceFrequency,
    StopLossType,
    strategy_simulator,
)

stock_pool_manager = stock_pool

__all__ = [
    "auto_trader",
    "stock_pool_manager",
    "risk_manager",
    "AutoTrader",
    "StockPool",
    "StockPosition",
    "stock_pool",
    "RiskManager",
    "StockPoolBuilder",
    "StockEntryMatrix",
    "EntryReason",
    "FilterCondition",
    "FactorCategory",
    "stock_pool_builder",
    "StrategySimulator",
    "SimulationConfig",
    "SimulationResult",
    "SimulatedPosition",
    "SimulatedTrade",
    "RebalanceFrequency",
    "StopLossType",
    "strategy_simulator",
]
