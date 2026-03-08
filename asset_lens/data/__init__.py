"""
Data module for asset-lens.
数据模块，包含数据模型和数据处理逻辑
"""

from .backtester import Backtester, BacktestResult, backtester
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
from .report_generator import InvestmentReportGenerator, investment_report_generator
from .risk_manager import RiskManager, risk_manager
from .scheduler import TaskScheduler, task_scheduler
from .stock_pool import StockPool, StockPosition, stock_pool
from .stock_screener import StockScreener, stock_screener
from .stock_tracker import StockTracker, stock_tracker
from .strategy_engine import StrategyConfig, StrategyEngine, strategy_engine

__all__ = [
    # Models
    "InvestmentProduct",
    "Transaction",
    "Portfolio",
    "InvestmentType",
    "RiskLevel",
    "Platform",
    "Currency",
    # Stock Pool
    "StockPool",
    "StockPosition",
    "stock_pool",
    # Strategy Engine
    "StrategyConfig",
    "StrategyEngine",
    "strategy_engine",
    # Stock Screener
    "StockScreener",
    "stock_screener",
    # Backtester
    "Backtester",
    "BacktestResult",
    "backtester",
    # Investment System
    "InvestmentSystem",
    "investment_system",
    # Stock Tracker
    "StockTracker",
    "stock_tracker",
    # Market Environment
    "MarketEnvironmentAnalyzer",
    "market_environment_analyzer",
    # Personal Data
    "PersonalDataIntegrator",
    "personal_data_integrator",
    # Scheduler
    "TaskScheduler",
    "task_scheduler",
    # Report Generator
    "InvestmentReportGenerator",
    "investment_report_generator",
    # Chart Generator
    "ChartGenerator",
    "chart_generator",
    # Risk Manager
    "RiskManager",
    "risk_manager",
]
