"""
Trading module - 交易相关功能
"""

from .auto_trader import AutoTrader, auto_trader
from .risk_manager import RiskManager, risk_manager
from .stock_pool import StockPool, StockPosition, stock_pool
from .stock_pool_builder import (
    EntryReason,
    FactorCategory,
    FilterCondition,
    StockEntryMatrix,
    StockPoolBuilder,
    stock_pool_builder,
)
from .strategy_simulator import (
    RebalanceFrequency,
    SimulatedPosition,
    SimulatedTrade,
    SimulationConfig,
    SimulationResult,
    StopLossType,
    StrategySimulator,
    strategy_simulator,
)

stock_pool_manager = stock_pool

__all__ = [
    "AutoTrader",
    "EntryReason",
    "FactorCategory",
    "FilterCondition",
    "RebalanceFrequency",
    "RiskManager",
    "SimulatedPosition",
    "SimulatedTrade",
    "SimulationConfig",
    "SimulationResult",
    "StockEntryMatrix",
    "StockPool",
    "StockPoolBuilder",
    "StockPosition",
    "StopLossType",
    "StrategySimulator",
    "auto_trader",
    "risk_manager",
    "stock_pool",
    "stock_pool_builder",
    "stock_pool_manager",
    "strategy_simulator",
]
