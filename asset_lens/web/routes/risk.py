"""
Risk API Routes - 风险相关 API
"""

from fastapi import APIRouter

from ...risk import risk_service

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("/summary")
async def get_risk_summary():
    """获取风险摘要"""
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
