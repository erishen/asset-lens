"""
System API Routes - 系统相关 API
"""

from fastapi import APIRouter, Query

from ...data.providers import provider_registry
from ...data.providers.cache import provider_cache

router = APIRouter(tags=["system"])


@router.get("/api/provider-health")
async def get_provider_health():
    """获取数据源健康状态"""
    try:
        summary = provider_registry.get_health_summary()
        return {"success": True, **summary}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/cache/stats")
async def get_cache_stats():
    """获取缓存统计"""
    try:
        stats = provider_cache.stats()
        return {"success": True, **stats}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/goals")
async def get_goals():
    """获取投资目标列表"""
    return {"success": True, "goals": [], "message": "Goals module deprecated"}


@router.post("/api/goals/add")
async def add_goal(
    name: str = Query(..., description="目标名称"),
    target_amount: float = Query(..., description="目标金额"),
    target_date: str = Query(..., description="目标日期 (YYYY-MM-DD)"),
    owner: str = Query("personal", description="所有者"),
    description: str = Query("", description="描述"),
):
    """添加投资目标"""
    return {"success": False, "message": "Goals module deprecated"}
