"""
Recommendation Routes - 推荐相关 API
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


class StockRecommendation(BaseModel):
    """股票推荐模型"""

    code: str
    name: str = ""
    score: float = 0
    reason: str = ""
    strategy_match: str = ""
    risk_level: str = ""
    confidence: float = 0


class StrategyRecommendation(BaseModel):
    """策略推荐模型"""

    strategy_name: str
    score: float = 0
    reason: str = ""
    expected_return: float = 0
    risk_level: str = ""
    confidence: float = 0


@router.get("/stocks")
async def recommend_stocks(
    strategy_name: str | None = None,
    max_stocks: int = Query(10, ge=1, le=50),
):
    """推荐股票"""
    from ...data.intelligent_recommender import intelligent_recommender

    recommendations = intelligent_recommender.recommend_stocks(
        strategy_name=strategy_name,
        max_stocks=max_stocks,
    )

    return {
        "strategy": strategy_name,
        "count": len(recommendations),
        "recommendations": [
            {
                "code": r.code,
                "name": r.name,
                "score": r.score,
                "reason": r.reason,
                "strategy_match": r.strategy_match,
                "risk_level": r.risk_level,
                "confidence": r.confidence,
            }
            for r in recommendations
        ],
    }


@router.get("/strategies")
async def recommend_strategies(
    risk_preference: str = Query("moderate", description="风险偏好"),
    investment_period: str = Query("medium", description="投资周期"),
):
    """推荐策略"""
    from ...data.intelligent_recommender import intelligent_recommender

    recommendations = intelligent_recommender.recommend_strategy(
        risk_preference=risk_preference,
        investment_period=investment_period,
    )

    return {
        "risk_preference": risk_preference,
        "investment_period": investment_period,
        "count": len(recommendations),
        "recommendations": [
            {
                "strategy_name": r.strategy_name,
                "score": r.score,
                "reason": r.reason,
                "expected_return": r.expected_return,
                "risk_level": r.risk_level,
                "confidence": r.confidence,
            }
            for r in recommendations
        ],
    }
