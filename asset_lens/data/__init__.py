"""
Data module for asset-lens.
数据模块，包含数据模型和数据处理逻辑
"""

from .chart_generator import ChartGenerator, chart_generator
from .investment_system import InvestmentSystem, investment_system
from .market_environment import MarketEnvironmentAnalyzer, market_environment_analyzer
from .models import (
    Currency,
    InvestmentProduct,
    InvestmentType,
    Platform,
    Portfolio,
    RiskLevel,
    Transaction,
)
from .personal_data_integrator import PersonalDataIntegrator, personal_data_integrator
from .scheduler import TaskScheduler, task_scheduler
from .stock_tracker import StockTracker, stock_tracker

from ..strategy import strategy_engine, backtester, stock_screener
from ..strategy.engine import StrategyConfig, StrategyEngine
from ..strategy.backtester import Backtester, BacktestResult
from ..strategy.screener import StockScreener
from ..trading import auto_trader, stock_pool_manager, risk_manager
from ..trading.stock_pool import StockPool, StockPosition, stock_pool
from ..trading.risk_manager import RiskManager

__all__ = [
    "InvestmentProduct",
    "Transaction",
    "Portfolio",
    "InvestmentType",
    "RiskLevel",
    "Platform",
    "Currency",
    "StockPool",
    "StockPosition",
    "stock_pool",
    "StrategyConfig",
    "StrategyEngine",
    "strategy_engine",
    "StockScreener",
    "stock_screener",
    "Backtester",
    "BacktestResult",
    "backtester",
    "InvestmentSystem",
    "investment_system",
    "StockTracker",
    "stock_tracker",
    "MarketEnvironmentAnalyzer",
    "market_environment_analyzer",
    "PersonalDataIntegrator",
    "personal_data_integrator",
    "TaskScheduler",
    "task_scheduler",
    "ChartGenerator",
    "chart_generator",
    "RiskManager",
    "risk_manager",
    "auto_trader",
    "stock_pool_manager",
]
