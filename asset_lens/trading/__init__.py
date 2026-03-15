"""
Trading module - 交易相关功能
"""

from .auto_trader import AutoTrader, auto_trader
from .stock_pool import StockPool, StockPosition, stock_pool
from .risk_manager import RiskManager, risk_manager

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
]
