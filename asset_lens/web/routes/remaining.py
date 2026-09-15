"""
Remaining Routes - 剩余资产盘点 API

覆盖理财 / 固收 / 权益三大透视之外的资产：货币基金、现金及外币、黄金、个人养老金。
收益率为持有期收益率，年化为 make analyze 同口径（360 天折算）。
"""

import os

from fastapi import APIRouter

from .equity import _is_equity_product
from .fixed_income import _is_fixed_income_product
from .wealth import WEALTH_TYPES

router = APIRouter(prefix="/api/remaining", tags=["remaining"])

DEMO_MODE = os.getenv("ASSET_LENS_DEMO_MODE", "").lower() in ("true", "1", "yes")


def _is_remaining_product(p) -> bool:
    """剩余资产 = 理财 / 固收 / 权益三大透视之外的产品"""
    if p.investment_type.value in WEALTH_TYPES:
        return False
    if _is_fixed_income_product(p):
        return False
    return not _is_equity_product(p)


def _classify_remaining(name: str, itype: str) -> str:
    """剩余资产子类：货币/现金 / 黄金 / 个人养老金"""
    if itype == "个人养老金":
        return "个人养老金"
    if itype == "黄金" or "黄金" in name:
        return "黄金"
    return "货币/现金"


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


def _load_remaining_products() -> list[dict]:
    from .portfolio import _load_portfolio_with_returns

    portfolio = _load_portfolio_with_returns()
    usd_rate, hkd_rate = _load_fx_rates()
    products = []
    for p in portfolio.products:
        if not _is_remaining_product(p):
            continue
        amount = float(p.current_amount or p.initial_amount or 0)
        held_days = p.investment_days
        itype = p.investment_type.value
        if itype == "现金（港元）":
            currency = "HKD"
        elif itype in ("现金（美元）", "美元基金（美元）") or "USD" in p.name or (itype == "其他" and "美元" in p.name):
            currency = "USD"
        else:
            currency = "CNY"
        fx_rate = usd_rate if currency == "USD" else (hkd_rate if currency == "HKD" else 1.0)
        holding_return = float(p.return_rate) if p.return_rate is not None else None
        annualized = float(p.annual_return) if p.annual_return is not None else None
        products.append(
            {
                "name": p.name,
                "type": itype,
                "category": _classify_remaining(p.name, itype),
                "risk_level": p.risk_level.value if p.risk_level else "-",
                "amount": round(amount, 2),
                "amount_cny": round(amount * fx_rate, 2),
                "annual_return": holding_return,
                "annualized_return": annualized,
                "held_days": held_days,
                "held_bucket": _held_bucket(held_days),
                "currency": currency,
            }
        )
    products.sort(key=lambda x: -x["amount_cny"])
    return products


def _generate_remaining_advice(products: list[dict]) -> list[dict]:
    """剩余资产视角建议：货币收益/现金效率/黄金波动/养老金长持"""
    advice: list[dict] = []
    total = sum(p["amount_cny"] for p in products)
    money_total = sum(p["amount_cny"] for p in products if p["category"] == "货币/现金")

    for p in products:
        annualized = p.get("annualized_return")
        ret = p.get("annual_return")
        amt = p["amount_cny"]
        base = {"product": p["name"], "product_type": p["type"], "amount": amt}

        if p["category"] == "货币/现金":
            if annualized is not None and annualized < 1.2:
                advice.append({**base, "priority": "medium", "type": "收益偏低",
                               "message": f"年化仅 {annualized}%，低于货基常见水平（~1.5%），可对比同类产品"})
            elif annualized is not None and annualized >= 2:
                advice.append({**base, "priority": "low", "type": "收益正常",
                               "message": f"年化 {annualized}%，货币类收益正常，保持流动性"})
            elif annualized is None and p["amount"] > 0:
                advice.append({**base, "priority": "low", "type": "活钱",
                               "message": "现金类无收益，保留用于日常流动性"})
        elif p["category"] == "黄金":
            if annualized is not None and annualized >= 10:
                advice.append({**base, "priority": "medium", "type": "涨幅较大",
                               "message": f"年化 {annualized}%，涨幅较大，注意回调风险与仓位控制"})
            elif ret is not None and ret < 0:
                advice.append({**base, "priority": "medium", "type": "浮亏",
                               "message": f"持有期 {ret}%，金价波动，评估持有成本与时机"})
            else:
                advice.append({**base, "priority": "low", "type": "持有",
                               "message": "黄金作为对冲资产持有，比例控制在组合 5%~10% 为宜"})
        elif p["category"] == "个人养老金":
            if annualized is not None and annualized >= 5:
                advice.append({**base, "priority": "low", "type": "长期增值",
                               "message": f"年化 {annualized}%，养老金账户长期持有，享受递延税收优惠"})
            else:
                advice.append({**base, "priority": "low", "type": "长持",
                               "message": "养老金账户封闭至退休，以长期定投/持有为主"})

    # 现金效率（整体）
    if total > 0:
        cash_ratio = money_total / total * 100
        if cash_ratio >= 60:
            advice.append({"product": "组合", "product_type": "现金效率", "amount": money_total,
                           "priority": "medium", "type": "现金占比高",
                           "message": f"货币/现金占剩余资产 {cash_ratio:.0f}%，若总额偏高可考虑转投短债/货基组合提升收益"})

    priority_order = {"high": 0, "medium": 1, "low": 2}
    advice.sort(key=lambda x: (priority_order.get(x["priority"], 9), -x["amount"]))
    return advice


@router.get("/overview")
async def remaining_overview():
    """剩余资产盘点汇总"""
    if DEMO_MODE:
        from ..demo_data import get_demo_remaining_overview

        return get_demo_remaining_overview()

    from .portfolio import _load_portfolio_with_returns

    products = _load_remaining_products()
    portfolio = _load_portfolio_with_returns()
    portfolio_total = float(portfolio.total_value)

    if not products or portfolio_total <= 0:
        return {
            "total_amount": 0, "ratio": 0, "product_count": 0,
            "avg_return": None, "avg_annualized": None, "negative_count": 0,
            "categories": [], "risk_distribution": {}, "held_distribution": {},
            "portfolio_insights": [], "advice": [], "products": [],
        }

    total = sum(p["amount_cny"] for p in products)

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

    risk_dist: dict[str, float] = {}
    held_dist: dict[str, float] = {}
    for p in products:
        risk_dist[p["risk_level"]] = round(risk_dist.get(p["risk_level"], 0.0) + p["amount_cny"], 2)
        held_dist[p["held_bucket"]] = round(held_dist.get(p["held_bucket"], 0.0) + p["amount_cny"], 2)

    negative = [p for p in products if p.get("annual_return") is not None and p["annual_return"] < 0]
    returns = [p["annual_return"] for p in products if p.get("annual_return") is not None]
    annualized_vals = [p["annualized_return"] for p in products if p.get("annualized_return") is not None]
    avg_return = sum(returns) / len(returns) if returns else None
    avg_annualized = sum(annualized_vals) / len(annualized_vals) if annualized_vals else None

    advice = _generate_remaining_advice(products)
    for p in products:
        matched = [a for a in advice if a["product"] == p["name"] and a.get("product_type") == p["type"]]
        p["detail"] = {
            "name": p["name"],
            "type_desc": f"{p['category']}（{p['type']}）",
            "annualized_return": p.get("annualized_return"),
            "advice": [{"priority": a["priority"], "type": a["type"], "message": a["message"]} for a in matched],
        }

    portfolio_insights: list[dict] = []
    money_cat = next((c for c in categories if c["name"] == "货币/现金"), None)
    if money_cat and money_cat["ratio"] >= 60:
        portfolio_insights.append({
            "level": "medium", "type": "现金占比",
            "message": f"货币/现金占剩余资产 {money_cat['ratio']:.0f}%，流动性充裕，可优化收益",
        })
    gold_cat = next((c for c in categories if c["name"] == "黄金"), None)
    if gold_cat:
        gold_total_ratio = gold_cat["amount"] / portfolio_total * 100 if portfolio_total else 0
        portfolio_insights.append({
            "level": "low", "type": "对冲资产",
            "message": f"黄金占总组合 {gold_total_ratio:.1f}%（剩余资产内 {gold_cat['ratio']:.0f}%），作为通胀对冲保持适度配置",
        })
    pension_cat = next((c for c in categories if c["name"] == "个人养老金"), None)
    if pension_cat:
        portfolio_insights.append({
            "level": "low", "type": "养老储备",
            "message": f"个人养老金占比 {pension_cat['ratio']:.0f}%，封闭至退休，享受递延税收优惠",
        })

    return {
        "total_amount": round(total, 2),
        "portfolio_total": round(portfolio_total, 2),
        "ratio": round(total / portfolio_total * 100, 1),
        "product_count": len(products),
        "avg_return": round(avg_return, 2) if avg_return is not None else None,
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
