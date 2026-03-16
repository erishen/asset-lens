"""
Web Routes Package - Web 路由模块
将 API 端点按功能分组
"""

from .compare import router as compare_router
from .risk import router as risk_router
from .system import router as system_router

__all__ = [
    "compare_router",
    "risk_router",
    "system_router",
]
