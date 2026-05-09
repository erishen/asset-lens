"""
Web Routes - API 路由模块
"""

from .backup import router as backup_router
from .chat import router as chat_router
from .compare import router as compare_router
from .market import router as market_router
from .ml import router as ml_router
from .portfolio import router as portfolio_router
from .recommendation import router as recommendation_router
from .report import router as report_router
from .risk import router as risk_router
from .stock import router as stock_router
from .stock_pool import router as stock_pool_router
from .strategy import router as strategy_router
from .system import router as system_router

__all__ = [
    "backup_router",
    "chat_router",
    "compare_router",
    "market_router",
    "ml_router",
    "portfolio_router",
    "recommendation_router",
    "report_router",
    "risk_router",
    "stock_pool_router",
    "stock_router",
    "strategy_router",
    "system_router",
]
