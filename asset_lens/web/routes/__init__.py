"""
Web Routes - API 路由模块
"""

from .compare import router as compare_router
from .market import router as market_router
from .portfolio import router as portfolio_router
from .risk import router as risk_router
from .stock import router as stock_router
from .strategy import router as strategy_router
from .system import router as system_router

__all__ = [
    "stock_router",
    "portfolio_router",
    "strategy_router",
    "market_router",
    "compare_router",
    "risk_router",
    "system_router",
]
