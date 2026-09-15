"""
Wealth Routes - 理财类产品风险透视 API

基于投资产品 CSV 中"理财/高端理财/券商理财"三类产品，
按发行机构、风险等级、期限结构、收益表现透视信用风险构成。
"""

import os
from datetime import date

from fastapi import APIRouter

router = APIRouter(prefix="/api/wealth", tags=["wealth"])

# Demo 模式检测
DEMO_MODE = os.getenv("ASSET_LENS_DEMO_MODE", "").lower() in ("true", "1", "yes")

WEALTH_TYPES = ("理财", "高端理财", "券商理财")

# 发行机构关键词 → 展示名（按优先级匹配产品名称）
INSTITUTION_RULES = [
    ("财达证券", "财达证券"),
    ("国泰海通", "国泰海通"),
    ("东方红", "东方红资管"),
    ("招银", "招银理财"),
    ("交银", "交银理财"),
    ("中银", "中银理财"),
    ("信银", "信银理财"),
    ("安盈象", "信银理财"),
    ("盈象", "信银理财"),
    ("建信", "建信理财"),
    ("农银", "农银理财"),
    ("工银", "工银理财"),
    ("阳光", "光大理财"),
    ("鹏华", "鹏华基金"),
]
DEFAULT_INSTITUTION = "其他/待标注"

# 平台列缩写 → 中文银行名
PLATFORM_NAMES = {
    "wechat": "微信",
    "cicc": "中金",
    "alipay": "支付宝",
    "futu": "富途",
    "cmb": "招商",
    "cmb_hk": "港招",
    "bocom": "交通",
    "spdb": "浦发",
    "ccb": "建设",
    "citic": "中信",
    "cmbc": "民生",
    "icbc": "工商",
    "boc": "中银",
}

# 券商渠道购买的权益型基金（指数增强/混合等公募基金，非理财）
EQUITY_FUND_KEYWORDS = ("指数", "增强", "混合", "股票", "沪深300", "ETF联接")

# 权益暴露关键词（理财名称含这些 → 有股票/指数敞口，风险更高）
EQUITY_EXPOSURE_KEYWORDS = ("混合", "指数", "增强", "权益", "FOF", "股票")

# CSV 风险等级基础分
RISK_LEVEL_BASE = {"低": 15, "中低": 30, "中": 55, "中高": 80, "高": 95}

# 机构知识库：发行机构全称 + 类型说明（用于详情弹窗）
INSTITUTION_INFO = {
    "财达证券": {"issuer": "财达证券股份有限公司", "kind": "券商资管", "note": "券商集合资产管理计划，非银行理财，管理人资质为证券公司"},
    "招银理财": {"issuer": "招银理财有限责任公司", "kind": "银行理财子公司", "note": "招商银行理财子公司，代销渠道含多家银行"},
    "交银理财": {"issuer": "交银理财有限责任公司", "kind": "银行理财子公司", "note": "交通银行理财子公司"},
    "中银理财": {"issuer": "中银理财有限责任公司", "kind": "银行理财子公司", "note": "中国银行理财子公司"},
    "信银理财": {"issuer": "信银理财有限责任公司", "kind": "银行理财子公司", "note": "中信银行理财子公司"},
    "建信理财": {"issuer": "建信理财有限责任公司", "kind": "银行理财子公司", "note": "建设银行理财子公司"},
    "农银理财": {"issuer": "农银理财有限责任公司", "kind": "银行理财子公司", "note": "农业银行理财子公司"},
    "工银理财": {"issuer": "工银理财有限责任公司", "kind": "银行理财子公司", "note": "工商银行理财子公司"},
    "光大理财": {"issuer": "光大理财有限责任公司", "kind": "银行理财子公司", "note": "光大银行理财子公司"},
    "鹏华基金": {"issuer": "鹏华基金管理有限公司", "kind": "公募基金", "note": "公募基金管理人，非银行理财"},
    "民生银行": {"issuer": "民生理财有限责任公司", "kind": "银行理财子公司", "note": "民生银行理财子公司，民生银行为代销渠道"},
    "浦发银行": {"issuer": "浦银理财有限责任公司", "kind": "银行理财子公司", "note": "浦发银行理财子公司"},
    "其他/待标注": {"issuer": "待确认", "kind": "未知", "note": "机构信息待标注"},
}

# 风险等级解读
RISK_LEVEL_NOTE = {
    "低": "低风险：本金损失可能性极低，净值基本稳定",
    "中低": "中低风险：投资风格稳健，本金损失可能性较低，净值可能小幅回撤",
    "中": "中等风险：净值波动加大，可能承受一定回撤，本金存在损失可能",
    "中高": "中高风险：净值波动明显，可能出现阶段性亏损",
    "高": "高风险：净值波动大，本金损失可能性高",
}


def _is_equity_fund(name: str) -> bool:
    return any(kw in name for kw in EQUITY_FUND_KEYWORDS)


def _held_bucket(held_days: int | None) -> str:
    """持有时间分桶"""
    if held_days is None:
        return "未知"
    if held_days < 90:
        return "新买入"
    if held_days < 180:
        return "短期"
    if held_days < 365:
        return "中期"
    return "长期"


def _compute_product_risk_score(
    name: str, risk_level: str, annual_return: float, amount: float, total: float, held_days: int | None
) -> tuple[int, list[str]]:
    """
    理财综合风险评分（0-100）——核心看信用风险信号：
    CSV 风险等级 + 收益异常（信用下沉） + 权益型暴露（轻度） + 金额集中 + 时间因素
    返回 (评分, 评分拆解原因列表)
    """
    reasons: list[str] = []
    score = RISK_LEVEL_BASE.get(risk_level, 30)
    reasons.append(f"风险等级「{risk_level}」基础分 {score}")

    # 收益异常（信用风险核心信号）：高收益往往对应信用下沉/配置更高风险资产；亏损已暴露风险
    if annual_return < 0:
        score += 20  # 已产生亏损
        reasons.append(f"年化 {annual_return}% 已亏损 +20")
    elif annual_return >= 3:
        score += 15  # 高收益 → 大概率信用下沉（底层非标/低等级信用债）
        reasons.append(f"年化 {annual_return}% ≥3% 高收益（信用下沉信号）+15")

    # 权益型理财（名称含混合/指数/权益/FOF/股票 → 真含权益敞口）轻度加分
    if any(kw in name for kw in ("混合", "指数", "权益", "FOF", "股票")):
        score += 10
        reasons.append("名称含混合/指数/权益等 → 权益型敞口 +10")
    elif "增强" in name:
        score += 5  # 固收增强（以固收为主，权益敞口小）
        reasons.append("固收增强（固收打底+少量权益增强）+5")

    if total > 0 and amount / total >= 0.2:
        score += 10  # 单产品占理财总额 ≥20%，集中风险
        reasons.append(f"单笔占理财总额 {amount / total * 100:.0f}% ≥20% 集中 +10")
    if held_days is not None and held_days < 90:
        score += 5  # 刚买入，收益未充分验证
        reasons.append(f"持有 {held_days} 天 <90 天（新买入）+5")
    return min(100, score), reasons


def _build_product_detail(p: dict, advice: list[dict]) -> dict:
    """生成产品详情（详情弹窗用）：机构知识库 + 评分拆解 + 关联建议"""
    inst_key = p["institution"] if p["institution"] in INSTITUTION_INFO else "其他/待标注"
    inst_info = INSTITUTION_INFO[inst_key]
    matched_advice = [a for a in advice if a["product"] == p["name"]]

    # 产品类型解读
    type_desc = "定期到期产品"
    if "持有" in p["name"]:
        type_desc = "持有期产品"
    elif "指数" in p["name"] or "混合" in p["name"] or "权益" in p["name"] or "FOF" in p["name"] or "股票" in p["name"]:
        type_desc = "权益型理财（含股票/指数/混合敞口）"
    elif "增强" in p["name"]:
        type_desc = "固收增强型（固收打底+少量权益增强）"
    elif p["term"] == "开放型":
        type_desc = "开放型理财（可随时申赎）"

    held_note = "未知"
    if p["held_days"] is not None:
        held_note = f"已持有 {p['held_days']} 天（{p['held_bucket']}）"
    maturity_note = "无固定到期日，可随时赎回" if not p["maturity"] or p["maturity"] == "可赎" else (
        f"{p['maturity']} 到期" + (
            f"（已到期 {-p['days_to_maturity']} 天，请确认回款）" if p["days_to_maturity"] is not None and p["days_to_maturity"] < 0
            else f"（剩 {p['days_to_maturity']} 天）" if p["days_to_maturity"] is not None
            else ""
        ) + ("，滚动续投" if p["is_rolling"] else "")
    )

    return {
        "name": p["name"],
        "issuer": inst_info["issuer"],
        "kind": inst_info["kind"],
        "inst_note": inst_info["note"],
        "type_desc": type_desc,
        "risk_note": RISK_LEVEL_NOTE.get(p["risk_level"], ""),
        "score_reasons": p.get("score_reasons", []),
        "held_note": held_note,
        "maturity_note": maturity_note,
        "advice": [{"priority": a["priority"], "type": a["type"], "message": a["message"]} for a in matched_advice],
    }


def _extract_institution(name: str, platform_amounts: dict | None = None) -> str:
    """优先按产品名称识别发行机构；名称未含机构时按购买平台（金额最大渠道）标注"""
    for keyword, label in INSTITUTION_RULES:
        if keyword in name:
            return label
    if platform_amounts:
        top_platform = max(platform_amounts.items(), key=lambda kv: float(kv[1] or 0))
        if float(top_platform[1] or 0) > 0:
            platform_name = PLATFORM_NAMES.get(top_platform[0], top_platform[0])
            return f"{platform_name}银行"
    return DEFAULT_INSTITUTION


def _classify_term(product) -> str:
    """期限结构：定期到期 / 持有期 / 开放型"""
    if product.maturity_date is not None:
        return "定期到期"
    if "持有" in product.name:
        return "持有期"
    return "开放型"


def _generate_advice(products: list[dict]) -> list[dict]:
    """生成调整建议（基于风险评分 + 到期状态 + 收益信号），按优先级排序"""
    advice: list[dict] = []

    # 1. 已到期未回款 → 最高优先级行动
    for p in products:
        if p["days_to_maturity"] is not None and p["days_to_maturity"] < 0:
            advice.append(
                {
                    "priority": "high",
                    "type": "到期处理",
                    "product": p["name"],
                    "amount": p["amount"],
                    "message": f"已到期 {-p['days_to_maturity']} 天未回款，请确认资金是否自动续期/已到账，并重新评估是否继续持有",
                }
            )

    # 2. 风险收益比不匹配：含权益敞口（混合/指数/权益/FOF/股票）但年化 <2%
    for p in products:
        if any(kw in p["name"] for kw in ("混合", "指数", "权益", "FOF", "股票")) and p["annual_return"] < 2:
            advice.append(
                {
                    "priority": "medium",
                    "type": "风险收益比",
                    "product": p["name"],
                    "amount": p["amount"],
                    "message": f"含权益敞口但年化仅 {p['annual_return']}%，收益配不上波动风险，可考虑置换为同机构纯固收理财",
                }
            )

    # 3. 大额即将到期（≥15% 且 30 天内）→ 到期重新决策
    total = sum(p["amount"] for p in products)
    for p in products:
        if (
            p["days_to_maturity"] is not None
            and 0 <= p["days_to_maturity"] <= 30
            and total > 0
            and p["amount"] / total >= 0.15
        ):
            advice.append(
                {
                    "priority": "medium",
                    "type": "大额到期",
                    "product": p["name"],
                    "amount": p["amount"],
                    "message": f"单笔占理财 {p['amount'] / total * 100:.0f}%，{p['days_to_maturity']} 天后到期（{'滚动续投' if p['is_rolling'] else '需手动决策'}），到期前请确认是否续投",
                }
            )

    # 4. 高收益信用下沉（年化 ≥3%）→ 了解底层
    for p in products:
        if p["annual_return"] >= 3:
            advice.append(
                {
                    "priority": "low",
                    "type": "信用下沉",
                    "product": p["name"],
                    "amount": p["amount"],
                    "message": f"年化 {p['annual_return']}% 为同类最高，大概率配置了更多非标/低等级信用债，建议了解底层资产再决定持有",
                }
            )

    priority_order = {"high": 0, "medium": 1, "low": 2}
    advice.sort(key=lambda x: (priority_order.get(x["priority"], 9), -x["amount"]))
    return advice


def _load_wealth_products() -> list[dict]:
    from .portfolio import _load_portfolio_with_returns

    portfolio = _load_portfolio_with_returns()
    products = []
    for p in portfolio.products:
        if p.investment_type.value not in WEALTH_TYPES:
            continue
        # 券商渠道权益型基金（指数增强/混合等公募基金）不归理财，已按基金统计
        if p.investment_type.value == "券商理财" and _is_equity_fund(p.name):
            continue
        amount = float(p.current_amount or p.initial_amount or 0)
        held_days = p.investment_days
        days_to_maturity = None
        if p.maturity_date is not None:
            days_to_maturity = (p.maturity_date - date.today()).days
        products.append(
            {
                "name": p.name,
                "type": p.investment_type.value,
                "institution": _extract_institution(p.name, p.platform_amounts),
                "risk_level": p.risk_level.value if p.risk_level else "-",
                "amount": round(amount, 2),
                "annual_return": round(float(p.annual_return or 0), 2),
                "term": _classify_term(p),
                "maturity": p.maturity_date.isoformat() if p.maturity_date else "可赎",
                "is_rolling": p.is_rolling,
                "held_days": held_days,
                "held_bucket": _held_bucket(held_days),
                "days_to_maturity": days_to_maturity,
            }
        )
    # 计算综合风险评分并按风险降序排列（高风险在前）
    total = sum(p["amount"] for p in products)
    for p in products:
        score, reasons = _compute_product_risk_score(
            p["name"], p["risk_level"], p["annual_return"], p["amount"], total, p["held_days"]
        )
        p["risk_score"] = score
        p["score_reasons"] = reasons
    products.sort(key=lambda x: (-x["risk_score"], -x["annual_return"]))
    return products


@router.get("/overview")
async def wealth_overview():
    """理财类产品风险透视汇总"""
    if DEMO_MODE:
        from ..demo_data import get_demo_wealth_overview

        return get_demo_wealth_overview()

    from .portfolio import _load_portfolio_with_returns

    products = _load_wealth_products()
    portfolio = _load_portfolio_with_returns()
    portfolio_total = float(portfolio.total_value)

    if not products or portfolio_total <= 0:
        return {
            "total_amount": 0,
            "ratio": 0,
            "product_count": 0,
            "avg_annual_return": 0,
            "negative_count": 0,
            "negative_products": [],
            "institutions": [],
            "risk_distribution": {},
            "term_distribution": {},
            "products": [],
        }

    total = sum(p["amount"] for p in products)

    # 发行机构分布
    inst_map: dict[str, dict] = {}
    for p in products:
        bucket = inst_map.setdefault(p["institution"], {"amount": 0.0, "count": 0})
        bucket["amount"] += p["amount"]
        bucket["count"] += 1
    institutions = [
        {"name": name, **bucket, "ratio": round(bucket["amount"] / total * 100, 1)}
        for name, bucket in inst_map.items()
    ]
    institutions.sort(key=lambda x: -x["amount"])

    # 风险等级分布
    risk_dist: dict[str, float] = {}
    for p in products:
        risk_dist[p["risk_level"]] = round(risk_dist.get(p["risk_level"], 0.0) + p["amount"], 2)

    # 期限结构分布
    term_dist: dict[str, float] = {}
    for p in products:
        term_dist[p["term"]] = round(term_dist.get(p["term"], 0.0) + p["amount"], 2)

    negative = [p for p in products if p["annual_return"] < 0]
    avg_annual = sum(p["annual_return"] for p in products) / len(products)

    # 持有时间分布
    held_dist: dict[str, float] = {}
    for p in products:
        held_dist[p["held_bucket"]] = round(held_dist.get(p["held_bucket"], 0.0) + p["amount"], 2)

    # 定期到期产品：已到期未回款 / 即将到期
    overdue = [
        {k: p[k] for k in ("name", "institution", "amount", "maturity", "days_to_maturity")}
        for p in products
        if p["days_to_maturity"] is not None and p["days_to_maturity"] < 0
    ]
    upcoming = [
        {k: p[k] for k in ("name", "institution", "amount", "maturity", "days_to_maturity")}
        for p in products
        if p["days_to_maturity"] is not None and 0 <= p["days_to_maturity"] <= 30
    ]

    # 生成调整建议，并为每个产品挂接详情
    advice = _generate_advice(products)
    for p in products:
        p["detail"] = _build_product_detail(p, advice)

    return {
        "total_amount": round(total, 2),
        "portfolio_total": round(portfolio_total, 2),
        "ratio": round(total / portfolio_total * 100, 1),
        "product_count": len(products),
        "avg_annual_return": round(avg_annual, 2),
        "negative_count": len(negative),
        "negative_products": negative,
        "institutions": institutions,
        "risk_distribution": risk_dist,
        "term_distribution": term_dist,
        "held_distribution": held_dist,
        "overdue_products": overdue,
        "upcoming_products": upcoming,
        "advice": advice,
        "products": products,
    }
