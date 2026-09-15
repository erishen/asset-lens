"""
Fixed Income Routes - 固收类资产（债券基金/特别国债/公募固收/美元债基金）透视 API

覆盖投资产品 CSV 中"债券/特别国债/公募固收/债券基金（美元）"类产品，
按资产类别、风险等级、收益分布透视。收益率为持有期收益率（与权益一致），
年化为 make analyze 同口径（360 天折算）。
"""

import os

from fastapi import APIRouter

router = APIRouter(prefix="/api/fixed-income", tags=["fixed-income"])

# Demo 模式检测
DEMO_MODE = os.getenv("ASSET_LENS_DEMO_MODE", "").lower() in ("true", "1", "yes")

# 固收类投资类型
FIXED_INCOME_TYPES = ("债券", "特别国债", "公募固收", "债券基金（美元）")

# CSV 风险等级基础分（固收多为低风险，评分仅供风险结构参考）
RISK_LEVEL_BASE = {"低": 15, "中低": 30, "中": 55, "中高": 80, "高": 95}


def _is_fixed_income_product(p) -> bool:
    """是否固收类产品（CSV 类型未映射到枚举的美元债基金按名称识别）"""
    if p.investment_type.value in FIXED_INCOME_TYPES:
        return True
    # CSV "债券基金（美元）"未映射枚举时落为"其他"，按名称兜底识别
    return p.investment_type.value == "其他" and "债" in p.name


def _classify_fi(name: str, itype: str) -> str:
    """固收子类：国债 / 美元债 / 公募固收 / 债券基金"""
    if itype == "特别国债":
        return "特别国债"
    if itype == "债券基金（美元）" or "美元" in name:
        return "美元债"
    if itype == "公募固收":
        return "公募固收"
    return "债券基金"


def _held_bucket(held_days: int | None) -> str:
    if held_days is None:
        return "未知"
    if held_days < 90:
        return "新买入"
    if held_days < 180:
        return "短期"
    if held_days < 365:
        return "中期"
    return "长期"


def _load_fx_rates() -> tuple[float, float]:
    """从资产汇总表最新行读美元/港元汇率（默认 6.7 / 0.86）"""
    import csv as csv_module
    from pathlib import Path

    from ...config import config

    data_dir = config.get_latest_data_dir()
    if not data_dir or not data_dir.is_dir():
        return 6.7, 0.86
    files = sorted(Path(data_dir).glob("资产汇总*.csv"))
    if not files:
        return 6.7, 0.86
    try:
        with open(files[0], encoding="utf-8-sig") as f:
            rows = list(csv_module.DictReader(f))
        if not rows:
            return 6.7, 0.86
        last = rows[-1]
        usd = (last.get("美元汇率") or "").strip()
        hkd = (last.get("港元汇率") or "").strip()
        return (float(usd) if usd else 6.7), (float(hkd) if hkd else 0.86)
    except (OSError, ValueError):
        return 6.7, 0.86


def _load_fi_products() -> list[dict]:
    from .portfolio import _load_portfolio_with_returns

    portfolio = _load_portfolio_with_returns()
    usd_rate, _hkd_rate = _load_fx_rates()
    products = []
    for p in portfolio.products:
        if not _is_fixed_income_product(p):
            continue
        amount = float(p.current_amount or p.initial_amount or 0)
        held_days = p.investment_days
        # CSV "债券基金（美元）"未映射枚举时落为"其他"，显示时还原类型
        itype = p.investment_type.value
        if itype == "其他" and "债" in p.name:
            itype = "债券基金（美元）"
        currency = "USD" if itype == "债券基金（美元）" else "CNY"
        fx_rate = usd_rate if currency == "USD" else 1.0
        holding_return = float(p.return_rate) if p.return_rate is not None else (float(p.annual_return or 0) if p.annual_return is not None else 0.0)
        annualized = float(p.annual_return or 0) if p.annual_return is not None else None
        products.append(
            {
                "name": p.name,
                "type": itype,
                "category": _classify_fi(p.name, itype),
                "risk_level": p.risk_level.value if p.risk_level else "-",
                "amount": round(amount, 2),
                "amount_cny": round(amount * fx_rate, 2),
                "annual_return": round(holding_return, 2),
                "annualized_return": round(annualized, 2) if annualized is not None else None,
                "held_days": held_days,
                "held_bucket": _held_bucket(held_days),
                "currency": currency,
            }
        )
    products.sort(key=lambda x: -x["amount_cny"])
    return products


def _generate_fi_advice(products: list[dict]) -> list[dict]:
    """固收视角建议：负收益/低收益（低于货基）/高收益（信用下沉）/美元债/集中"""
    advice: list[dict] = []
    total = sum(p.get("amount_cny") or p["amount"] for p in products)
    for p in products:
        ret = p["annual_return"]
        annualized = p.get("annualized_return")
        amt = p.get("amount_cny") or p["amount"]
        base = {"product": p["name"], "product_type": p["type"], "amount": amt}

        # 1. 负收益（持有期）
        if ret < 0:
            advice.append({**base, "priority": "high", "type": "负收益",
                           "message": f"持有期收益 {ret}%，债市波动或含权益敞口，评估是否继续持有"})
        # 2. 低收益（年化 < 1.5%，低于常见货基）
        elif annualized is not None and annualized < 1.5:
            advice.append({**base, "priority": "medium", "type": "低收益",
                           "message": f"年化仅 {annualized}%，低于货币基金水平，考虑换更高收益固收"})
        # 3. 高收益（年化 >= 4%，信用下沉信号）
        if annualized is not None and annualized >= 4:
            advice.append({**base, "priority": "medium", "type": "高收益关注",
                           "message": f"年化 {annualized}% 高于一般债基，注意信用下沉/久期风险"})
        # 4. 美元债：汇率 + 美债利率
        if p["category"] == "美元债":
            advice.append({**base, "priority": "low", "type": "美元债",
                           "message": "美元计价，收益含汇率变动，关注美债利率与美元走势"})
        # 5. 集中度
        if total > 0 and amt / total >= 0.25:
            advice.append({**base, "priority": "medium", "type": "集中风险",
                           "message": f"单笔占固收总额 {amt / total * 100:.0f}%，持仓集中，注意单一产品风险"})
        # 6. 兜底：正常持有
        if not any(a["product"] == p["name"] and a["product_type"] == p["type"] for a in advice):
            advice.append({**base, "priority": "low", "type": "持有",
                           "message": f"年化 {annualized or ret}%，收益平稳，维持持有"})

    priority_order = {"high": 0, "medium": 1, "low": 2}
    advice.sort(key=lambda x: (priority_order.get(x["priority"], 9), -x["amount"]))
    return advice


@router.get("/overview")
async def fixed_income_overview():
    """固收类资产透视汇总"""
    if DEMO_MODE:
        from ..demo_data import get_demo_fixed_income_overview

        return get_demo_fixed_income_overview()

    from .portfolio import _load_portfolio_with_returns

    products = _load_fi_products()
    portfolio = _load_portfolio_with_returns()
    portfolio_total = float(portfolio.total_value)

    if not products or portfolio_total <= 0:
        return {
            "total_amount": 0, "ratio": 0, "product_count": 0,
            "avg_return": 0, "avg_annualized": 0, "negative_count": 0,
            "categories": [], "risk_distribution": {}, "held_distribution": {},
            "advice": [], "products": [],
        }

    total = sum(p["amount_cny"] for p in products)

    # 类别分布
    cat_map: dict[str, dict] = {}
    for p in products:
        bucket = cat_map.setdefault(p["category"], {"amount": 0.0, "count": 0})
        bucket["amount"] += p["amount_cny"]
        bucket["count"] += 1
    categories = [
        {"name": name, **bucket, "ratio": round(bucket["amount"] / total * 100, 1)}
        for name, bucket in cat_map.items()
    ]
    categories.sort(key=lambda x: -x["amount"])

    # 风险/持有分布
    risk_dist: dict[str, float] = {}
    held_dist: dict[str, float] = {}
    for p in products:
        risk_dist[p["risk_level"]] = round(risk_dist.get(p["risk_level"], 0.0) + p["amount_cny"], 2)
        held_dist[p["held_bucket"]] = round(held_dist.get(p["held_bucket"], 0.0) + p["amount_cny"], 2)

    # 收益汇总
    negative = [p for p in products if p["annual_return"] < 0]
    avg_return = sum(p["annual_return"] for p in products) / len(products)
    annualized_vals = [p["annualized_return"] for p in products if p["annualized_return"] is not None]
    avg_annualized = sum(annualized_vals) / len(annualized_vals) if annualized_vals else None

    # 建议
    advice = _generate_fi_advice(products)
    for p in products:
        matched = [a for a in advice if a["product"] == p["name"] and a.get("product_type") == p["type"]]
        p["detail"] = {
            "name": p["name"],
            "type_desc": f"{p['category']}（{p['type']}）",
            "annualized_return": p.get("annualized_return"),
            "advice": [{"priority": a["priority"], "type": a["type"], "message": a["message"]} for a in matched],
        }

    # 组合层面观察（固收视角）
    portfolio_insights: list[dict] = []
    if avg_annualized is not None:
        if avg_annualized < 1.5:
            portfolio_insights.append({
                "level": "medium", "type": "整体收益",
                "message": f"固收组合平均年化 {avg_annualized:.2f}%，低于货基水平，考虑优化结构",
            })
        elif avg_annualized >= 4:
            portfolio_insights.append({
                "level": "low", "type": "整体收益",
                "message": f"固收组合平均年化 {avg_annualized:.2f}%，收益偏高，留意信用下沉风险",
            })
    if negative:
        portfolio_insights.append({
            "level": "medium", "type": "负收益面",
            "message": f"{len(negative)} 个固收产品持有期负收益，多为债市波动或含权益/汇率敞口",
        })
    if categories:
        top_cat = categories[0]
        if top_cat["ratio"] >= 50:
            portfolio_insights.append({
                "level": "low", "type": "类别集中",
                "message": f"{top_cat['name']}占固收总额 {top_cat['ratio']:.0f}%，结构相对集中",
            })

    return {
        "total_amount": round(total, 2),
        "portfolio_total": round(portfolio_total, 2),
        "ratio": round(total / portfolio_total * 100, 1),
        "product_count": len(products),
        "avg_return": round(avg_return, 2),
        "avg_annualized": round(avg_annualized, 2) if avg_annualized is not None else None,
        "negative_count": len(negative),
        "negative_products": [{"name": p["name"], "annual_return": p["annual_return"], "amount_cny": p["amount_cny"]} for p in negative],
        "categories": categories,
        "risk_distribution": risk_dist,
        "held_distribution": held_dist,
        "portfolio_insights": portfolio_insights,
        "advice": advice,
        "products": products,
    }
