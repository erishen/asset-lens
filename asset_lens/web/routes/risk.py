"""
Risk API Routes - 风险相关 API
"""

import os

from fastapi import APIRouter

router = APIRouter(prefix="/api/risk", tags=["risk"])

# Demo 模式检测
DEMO_MODE = os.getenv("ASSET_LENS_DEMO_MODE", "").lower() in ("true", "1", "yes")


@router.get("/summary")
async def get_risk_summary():
    """获取风险摘要"""
    # Demo 模式下返回模拟风险数据
    if DEMO_MODE:
        from ..demo_data import get_demo_risk_summary
        return get_demo_risk_summary()

    from ...risk import risk_service

    try:
        summary = risk_service.get_risk_summary()

        return {
            "risk_score": summary.get("risk_score", 0),
            "risk_level": summary.get("risk_level", "unknown"),
            "total_position": summary.get("total_position", 0),
            "warnings": summary.get("warnings", []),
            "suggestions": summary.get("suggestions", []),
        }
    except (ValueError, KeyError, RuntimeError) as e:
        return {"error": str(e)}
