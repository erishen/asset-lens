"""
Strategy Routes - 策略相关 API
"""

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/strategies", tags=["strategy"])

# Demo 模式检测
DEMO_MODE = os.getenv("ASSET_LENS_DEMO_MODE", "").lower() in ("true", "1", "yes")


class StrategyInfo(BaseModel):
    """策略信息模型"""

    name: str
    description: str = ""
    buy_conditions: int = 0
    sell_conditions: int = 0
    position_size: float = 0
    max_positions: int = 0
    stop_loss: float = 0
    take_profit: float = 0


@router.get("", response_model=list[StrategyInfo])
async def list_strategies():
    """获取策略列表"""
    # Demo 模式下返回模拟数据
    if DEMO_MODE:
        from ..demo_data import get_demo_strategies
        strategies = get_demo_strategies()
        return [
            StrategyInfo(
                name=s["name"],
                description=s["description"],
                buy_conditions=s["buy_conditions"],
                sell_conditions=s["sell_conditions"],
                position_size=s["position_size"],
                max_positions=s["max_positions"],
                stop_loss=s["stop_loss"],
                take_profit=s["take_profit"],
            )
            for s in strategies
        ]

    from ...strategy.engine import strategy_engine

    strategies = strategy_engine.list_strategies()

    result = []
    for s in strategies:
        buy_cond = s.get("buy_conditions", [])
        sell_cond = s.get("sell_conditions", [])

        buy_count = buy_cond if isinstance(buy_cond, int) else len(buy_cond)
        sell_count = sell_cond if isinstance(sell_cond, int) else len(sell_cond)

        result.append(
            StrategyInfo(
                name=s.get("name", ""),
                description=s.get("description", ""),
                buy_conditions=buy_count,
                sell_conditions=sell_count,
                position_size=s.get("position_size", 0),
                max_positions=s.get("max_positions", 0),
                stop_loss=s.get("stop_loss", 0),
                take_profit=s.get("take_profit", 0),
            )
        )

    return result


@router.get("/{strategy_name}")
async def get_strategy(strategy_name: str):
    """获取策略详情"""
    # Demo 模式下返回模拟数据
    if DEMO_MODE:
        from ..demo_data import get_demo_strategy_detail
        strategy = get_demo_strategy_detail(strategy_name)
        if strategy is None:
            raise HTTPException(status_code=404, detail=f"策略 {strategy_name} 不存在")
        return {
            "name": strategy["name"],
            "description": strategy["description"],
            "buy_conditions": [{"name": f"条件{i+1}", "weight": 0.3, "value": True} for i in range(strategy["buy_conditions"])],
            "sell_conditions": [{"name": f"条件{i+1}", "weight": 0.3, "value": True} for i in range(strategy["sell_conditions"])],
            "position_size": strategy["position_size"],
            "max_positions": strategy["max_positions"],
            "stop_loss": strategy["stop_loss"],
            "take_profit": strategy["take_profit"],
        }

    from ...strategy.engine import strategy_engine

    strategy = strategy_engine.get_strategy(strategy_name)

    if strategy is None:
        raise HTTPException(status_code=404, detail=f"策略 {strategy_name} 不存在")

    return {
        "name": strategy.name,
        "description": strategy.description,
        "buy_conditions": [{"name": c.name, "weight": c.weight, "value": c.value} for c in strategy.buy_conditions],
        "sell_conditions": [{"name": c.name, "weight": c.weight, "value": c.value} for c in strategy.sell_conditions],
        "position_size": strategy.position_size,
        "max_positions": strategy.max_positions,
        "stop_loss": strategy.stop_loss,
        "take_profit": strategy.take_profit,
    }


@router.post("/{strategy_name}/evaluate/{code}")
async def evaluate_stock(strategy_name: str, code: str):
    """
    使用策略评估股票

    Args:
        strategy_name: 策略名称
        code: 股票代码
    """
    from ...strategy.engine import strategy_engine

    try:
        result = strategy_engine.evaluate_stock({"code": code}, strategy_name)
        return {
            "strategy": strategy_name,
            "code": code,
            "result": result,
        }
    except (ValueError, KeyError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=f"评估失败: {e!s}") from e


@router.get("/recommendations/stocks")
async def recommend_stocks(
    strategy_name: str = "momentum",
    limit: int = 10,
):
    """
    获取策略推荐的股票

    Args:
        strategy_name: 策略名称
        limit: 返回数量
    """
    from ...strategy.screener import stock_screener

    try:
        stocks = stock_screener.screen(filter_type="comprehensive")
        return {
            "strategy": strategy_name,
            "count": len(stocks[:limit]),
            "recommendations": stocks[:limit],
        }
    except (ValueError, KeyError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=f"获取推荐失败: {e!s}") from e
