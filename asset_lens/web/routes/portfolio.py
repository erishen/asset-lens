"""
Portfolio Routes - 投资组合相关 API
"""

import os
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...config import config

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

# CSV 解析结果缓存：按最新数据目录 + 目录内 CSV 最大 mtime 失效。
# 收益率为每次请求现算（幂等覆盖），缓存只省掉重复的文件读取与解析。
_products_cache: dict = {"key": None, "products": None}


def _load_products_cached():
    """加载原始产品列表（带缓存，数据目录或其 CSV 变更时自动失效）。"""
    from ...data.csv_parser import CSVParser

    data_dir = config.get_latest_data_dir()
    if data_dir is None or not data_dir.exists():
        return CSVParser.load_data()
    try:
        mtime = max(p.stat().st_mtime for p in data_dir.glob("*.csv"))
    except OSError:
        return CSVParser.load_data()
    key = (str(data_dir), mtime)
    if _products_cache["key"] == key:
        return _products_cache["products"]
    products = CSVParser.load_data()
    _products_cache["key"] = key
    _products_cache["products"] = products
    return products


def _load_portfolio_with_returns():
    """
    加载投资组合并现算每产品收益率（与 `make analyze` / `make calculate` 同口径）。

    1. CSVParser.load_data() 读取 ts-demo 宽表 CSV
    2. InvestmentCalculator.calculate_product_returns 现算 return_rate / annual_return
    3. Portfolio 汇总 total_value / total_initial / total_profit / overall_return_rate
       （总收益 = Σ(当前金额 - 初始金额) × 汇率，非手填"收益金额"列）
    """
    from datetime import datetime

    from ...data.models import Portfolio
    from ...data.parsers.investment_calculator import InvestmentCalculator

    products = _load_products_cached()
    portfolio = Portfolio(
        products=products,
        usd_rate=Decimal(str(config.default_usd_rate)),
        hkd_rate=Decimal(str(config.default_hkd_rate)),
    )
    reference_date = datetime.now()
    for product in portfolio.products:
        InvestmentCalculator.calculate_product_returns(product, reference_date)
    return portfolio


def _product_currency(product, portfolio) -> str:
    """识别产品币种（类型 + 名称兜底，与 AnalysisEvaluation 一致）"""
    from ...data.models import InvestmentType

    if product.investment_type in [InvestmentType.US_STOCK, InvestmentType.USD_FUND]:
        return "USD"
    if product.investment_type in [InvestmentType.HK_STOCK, InvestmentType.HK_CASH, InvestmentType.HK_DIVIDEND_FUND]:
        return "HKD"
    type_str = product.investment_type.value if product.investment_type else ""
    name = product.name or ""
    if "美元" in type_str or "美元" in name or "USD" in name.upper():
        return "USD"
    if "港元" in type_str or "港元" in name or "HKD" in name.upper():
        return "HKD"
    return "CNY"


def _converted_amount(product, portfolio) -> float:
    """当前金额换算人民币"""
    cur = _product_currency(product, portfolio)
    amount = product.current_amount or Decimal("0")
    if cur == "USD":
        return float(amount * (product.usd_rate or portfolio.usd_rate))
    if cur == "HKD":
        return float(amount * (product.hkd_rate or portfolio.hkd_rate))
    return float(amount)


def _converted_profit(product, portfolio) -> float:
    """单产品收益（换算人民币）：(当前金额 - 初始金额) × 汇率，与 Portfolio.total_profit 口径一致"""
    cur = _product_currency(product, portfolio)

    current = product.current_amount or Decimal("0")
    initial = product.initial_amount if product.start_date and product.initial_amount else current

    if cur == "USD":
        rate = product.usd_rate or portfolio.usd_rate
        current = current * rate
        initial = initial * rate
    elif cur == "HKD":
        rate = product.hkd_rate or portfolio.hkd_rate
        current = current * rate
        initial = initial * rate

    return float(current - initial)


def _converted_initial(product, portfolio) -> float:
    """初始投入换算人民币（与 current_amount / profit_amount 同口径）"""
    cur = _product_currency(product, portfolio)
    initial = product.initial_amount or Decimal("0")
    if cur == "USD":
        return float(initial * (product.usd_rate or portfolio.usd_rate))
    if cur == "HKD":
        return float(initial * (product.hkd_rate or portfolio.hkd_rate))
    return float(initial)

# Demo 模式检测
DEMO_MODE = os.getenv("ASSET_LENS_DEMO_MODE", "").lower() in ("true", "1", "yes")


class PortfolioSummary(BaseModel):
    """投资组合摘要模型"""

    total_assets: float = 0
    total_assets_overview: float = 0
    total_profit: float = 0
    total_return: float = 0
    realized_profit: float = 0
    unrealized_profit: float = 0
    position_count: int = 0
    data_dir: str = ""
    data_as_of: str = ""


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
    # Demo 模式下返回模拟数据
    if DEMO_MODE:
        from ..demo_data import get_demo_portfolio_summary

        data = get_demo_portfolio_summary()
        return PortfolioSummary(**data)

    try:
        portfolio = _load_portfolio_with_returns()

        # 加载卖出记录（已实现收益），与 make analyze 同口径
        from ...data.sell_record_parser import SellRecordParser

        try:
            sell_records = SellRecordParser.load_sell_records()
        except (OSError, ValueError, KeyError, TypeError):
            sell_records = []

        from ...report.analyzer import ReportGenerator

        report = ReportGenerator().generate_analysis_report(portfolio, sell_records)
        eval_data = report["comprehensive_evaluation"]

        total_assets = round(float(Decimal(eval_data["total_current_amount"])), 2)
        unrealized = Decimal(eval_data["unrealized_profit"])
        realized = Decimal(eval_data["realized_profit"])
        total_profit = round(float(unrealized + realized), 2)
        total_return = round(float(Decimal(eval_data["overall_return_rate"].rstrip("%"))), 2)

        data_dir = config.get_latest_data_dir()
        data_name = data_dir.name if data_dir else ""
        data_as_of = ""
        if data_name:
            import re as _re

            m = _re.search(r"(\d{8})", data_name)
            if m:
                d = m.group(1)
                data_as_of = f"{d[:4]}-{d[4:6]}-{d[6:]}"

        return PortfolioSummary(
            total_assets=total_assets,
            total_assets_overview=_load_total_assets_overview(),
            total_profit=total_profit,
            total_return=total_return,
            realized_profit=float(Decimal(eval_data["realized_profit"])),
            unrealized_profit=float(Decimal(eval_data["unrealized_profit"])),
            position_count=len(portfolio.products),
            data_dir=data_name,
            data_as_of=data_as_of,
        )

    except (ValueError, KeyError, TypeError, OSError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def _load_total_assets_overview() -> float:
    """读取资产汇总表末行总金额（全口径总资产，含现金/平台/三金/房产等）"""
    import csv as csv_module
    from pathlib import Path

    data_dir = Path(config.real_data_path)
    if not data_dir.is_dir():
        return 0.0

    files = sorted(data_dir.glob("资产汇总*.csv"))
    if not files:
        return 0.0

    try:
        with open(files[0], encoding="utf-8-sig") as f:
            rows = list(csv_module.DictReader(f))
        if not rows:
            return 0.0
        raw = (rows[-1].get("总金额") or "").strip()
        return round(float(raw), 2) if raw else 0.0
    except (OSError, ValueError, KeyError, TypeError):
        return 0.0


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
    # Demo 模式下返回模拟数据
    if DEMO_MODE:
        from ..demo_data import get_demo_portfolio_items

        return get_demo_portfolio_items(investment_type, sort_by, sort_order)

    try:
        portfolio = _load_portfolio_with_returns()

        items = []
        for p in portfolio.products:
            if investment_type and p.investment_type.value != investment_type:
                continue

            items.append(
                {
                    "name": p.name,
                    "code": "",
                    "investment_type": p.investment_type.value,
                    "risk_level": p.risk_level.value if p.risk_level else "-",
                    "currency": _product_currency(p, portfolio),
                    "current_amount": round(_converted_amount(p, portfolio), 2),
                    "original_amount": round(float(p.current_amount or 0), 2),
                    "initial_amount": round(_converted_initial(p, portfolio), 2),
                    "profit_amount": round(_converted_profit(p, portfolio), 2),
                    "return_rate": round(float(p.return_rate or 0), 2),
                    "annual_return": round(float(p.annual_return or 0), 2),
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

    except (ValueError, KeyError, TypeError, OSError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


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
    # Demo 模式下返回模拟数据
    if DEMO_MODE:
        from ..demo_data import get_demo_performance

        return get_demo_performance()

    from ...data.sell_record_parser import SellRecordParser
    from ...report.analyzer import ReportGenerator

    try:
        portfolio = _load_portfolio_with_returns()

        try:
            sell_records = SellRecordParser.load_sell_records()
        except (OSError, ValueError, KeyError, TypeError):
            sell_records = []

        analyzer = ReportGenerator()
        report = analyzer.generate_analysis_report(portfolio, sell_records)
        top_performers = report.get("top_performers", [])[:5]
        eval_data = report["comprehensive_evaluation"]

        total_assets = round(float(Decimal(eval_data["total_current_amount"])), 2)
        total_profit = round(float(Decimal(eval_data["unrealized_profit"]) + Decimal(eval_data["realized_profit"])), 2)
        total_return = round(float(Decimal(eval_data["overall_return_rate"].rstrip("%"))), 2)

        return {
            "summary": {
                "total_assets": total_assets,
                "total_profit": total_profit,
                "total_return": total_return,
                "position_count": len(portfolio.products),
            },
            "top_performers": top_performers,
            "evaluation": eval_data,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except (ValueError, KeyError, TypeError, OSError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
