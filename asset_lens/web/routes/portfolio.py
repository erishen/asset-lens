"""
Portfolio Routes - 投资组合相关 API
"""

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...config import config

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


class PortfolioSummary(BaseModel):
    """投资组合摘要模型"""

    total_assets: float = 0
    total_profit: float = 0
    total_return: float = 0
    position_count: int = 0


class PortfolioItem(BaseModel):
    """投资组合项目模型"""

    name: str
    code: str = ""
    investment_type: str = ""
    risk_level: str = ""
    current_amount: float = 0
    initial_amount: float = 0
    profit_amount: float = 0
    return_rate: float = 0
    annual_return: float = 0


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary():
    """获取投资组合摘要"""
    from ...data.csv_parser import CSVParser
    from ...data.models import Portfolio

    try:
        products = CSVParser.load_data()
        portfolio = Portfolio(
            products=products,
            usd_rate=Decimal(str(config.default_usd_rate)),
            hkd_rate=Decimal(str(config.default_hkd_rate)),
        )

        total_assets = sum(float(p.current_amount or 0) for p in portfolio.products)
        total_profit = sum(float(p.profit_amount or 0) for p in portfolio.products)
        total_return = (total_profit / total_assets * 100) if total_assets > 0 else 0

        return PortfolioSummary(
            total_assets=total_assets,
            total_profit=total_profit,
            total_return=total_return,
            position_count=len(portfolio.products),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items")
async def get_portfolio_items(
    investment_type: str | None = Query(None, description="投资类型筛选"),
    sort_by: str = Query("return_rate", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向 asc/desc"),
):
    """
    获取投资组合项目列表

    Args:
        investment_type: 投资类型筛选
        sort_by: 排序字段
        sort_order: 排序方向
    """
    from ...data.csv_parser import CSVParser

    try:
        products = CSVParser.load_data()

        items = []
        for p in products:
            if investment_type and p.investment_type.value != investment_type:
                continue

            items.append(
                {
                    "name": p.name,
                    "code": "",
                    "investment_type": p.investment_type.value,
                    "risk_level": p.risk_level.value if p.risk_level else "-",
                    "current_amount": float(p.current_amount or 0),
                    "initial_amount": float(p.initial_amount or 0),
                    "profit_amount": float(p.profit_amount or 0),
                    "return_rate": float(p.return_rate or 0),
                    "annual_return": float(p.annual_return or 0),
                }
            )

        reverse = sort_order.lower() == "desc"
        items.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

        return {
            "total": len(items),
            "investment_type": investment_type,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "items": items,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_portfolio_performance(
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
):
    """
    获取投资组合绩效分析

    Args:
        start_date: 开始日期
        end_date: 结束日期
    """
    from ...data.csv_parser import CSVParser
    from ...data.models import Portfolio
    from ...report.analyzer import ReportGenerator

    try:
        products = CSVParser.load_data()
        portfolio = Portfolio(
            products=products,
            usd_rate=Decimal(str(config.default_usd_rate)),
            hkd_rate=Decimal(str(config.default_hkd_rate)),
        )

        analyzer = ReportGenerator()
        report = analyzer.generate_analysis_report(portfolio)
        top_performers = report.get("top_performers", [])[:5]

        total_assets = sum(float(p.current_amount or 0) for p in portfolio.products)
        total_profit = sum(float(p.profit_amount or 0) for p in portfolio.products)
        total_return = (total_profit / total_assets * 100) if total_assets > 0 else 0

        return {
            "summary": {
                "total_assets": total_assets,
                "total_profit": total_profit,
                "total_return": total_return,
                "position_count": len(portfolio.products),
            },
            "top_performers": top_performers,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
