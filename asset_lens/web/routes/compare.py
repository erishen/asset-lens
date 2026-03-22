"""
Compare API Routes - 对比分析相关 API
"""

from fastapi import APIRouter, Query

from ...data.comparison import portfolio_comparator
from ...data.csv_parser import CSVParser
from ...data.snapshot import snapshot_manager

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.get("/weekly")
async def compare_weekly():
    """周度对比"""
    try:
        result = portfolio_comparator.compare_weekly()
        if result is None:
            return {"success": False, "message": "数据不足，无法进行周度对比"}
        return {"success": True, "comparison": result.to_dict()}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/periods")
async def compare_periods(
    date1: str = Query(..., description="起始日期 (YYYY-MM-DD)"),
    date2: str = Query(..., description="结束日期 (YYYY-MM-DD)"),
):
    """对比指定日期"""
    try:
        result = portfolio_comparator.compare_periods(date1, date2)
        if result is None:
            return {"success": False, "message": f"找不到 {date1} 或 {date2} 的快照数据"}
        return {"success": True, "comparison": result.to_dict()}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/trend")
async def get_trend_analysis(days: int = Query(30, description="分析天数")):
    """获取趋势分析"""
    try:
        result = portfolio_comparator.get_trend_analysis(days)
        return {"success": True, "trend": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/snapshot/create")
async def create_snapshot():
    """创建投资组合快照"""
    try:
        products = CSVParser.load_data()
        total_assets = sum(float(p.current_amount or 0) for p in products)
        total_initial = sum(float(p.initial_amount or 0) for p in products)
        total_profit = total_assets - total_initial
        return_rate = (total_profit / total_initial * 100) if total_initial > 0 else 0

        positions = [
            {
                "code": getattr(p, 'code', ''),
                "name": p.name,
                "amount": float(p.current_amount or 0),
                "profit": float(p.profit_amount or 0),
                "return_rate": float(p.return_rate or 0),
            }
            for p in products
        ]

        snapshot = snapshot_manager.create_snapshot(
            total_assets=total_assets,
            total_profit=total_profit,
            return_rate=return_rate,
            position_count=len(products),
            positions=positions,
        )

        return {
            "success": True,
            "snapshot_id": snapshot.snapshot_id,
            "timestamp": snapshot.timestamp,
            "total_assets": snapshot.total_assets,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/snapshot/list")
async def list_snapshots(count: int = Query(7, description="返回数量")):
    """获取快照列表"""
    try:
        snapshots = snapshot_manager.get_latest_snapshots(count)
        return {
            "success": True,
            "count": len(snapshots),
            "snapshots": [
                {
                    "snapshot_id": s.snapshot_id,
                    "timestamp": s.timestamp,
                    "total_assets": s.total_assets,
                    "return_rate": s.return_rate,
                    "position_count": s.position_count,
                }
                for s in snapshots
            ],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
