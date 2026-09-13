"""
Risk API Routes - 风险相关 API

基于个人投资组合真实数据计算组合风险（与 make analyze 同数据源），
替代原先股票池交易风险（与个人资产无关）及前端写死的默认值。
"""

import os
from decimal import Decimal

from fastapi import APIRouter

router = APIRouter(prefix="/api/risk", tags=["risk"])

# Demo 模式检测
DEMO_MODE = os.getenv("ASSET_LENS_DEMO_MODE", "").lower() in ("true", "1", "yes")

# 类型流动性系数（变现速度：1.0=随时可用，0=完全锁定）
LIQUIDITY_FACTORS = {
    "货币": 1.0,  # 货币基金 T+0/T+1
    "现金": 1.0,
    "现金（港元）": 1.0,
    "ETF": 0.9,  # 场内 T+1
    "黄金": 0.9,  # 黄金交易日可直接买卖（场内）
    "美股": 0.8,  # T+1 可卖，跨境到账慢
    "港股": 0.8,
    "基金": 0.8,  # 股票型/混合型基金，T+2 可赎回
    "债券基金": 0.8,  # 债基 T+2 可赎回
    "定投基金": 0.8,  # 基金形式，T+2 可赎回
    "美元基金（美元）": 0.5,  # 跨境美元基金，赎回到账较慢（T+3~T+7）
    "股息基金（港元）": 0.5,  # 跨境港元基金，赎回到账较慢
    "QDII": 0.4,  # QDII 基金，确认+到账最慢（T+5~T+10）
    "公募固收": 0.8,  # 债基 T+1~T+7 赎回
    "债券": 0.7,  # 场外债/可转债
    "特别国债": 0.6,  # 二级市场可卖，可能折价
    "其他": 0.5,
    "理财": 0.4,  # 多数封闭期或需预约
    "高端理财": 0.4,
    "券商理财": 0.4,
    "个人养老金": 0.05,  # 封闭到退休
}

# 券商渠道购买的权益型基金（名称含指数/增强/混合/股票等，本质是公募基金而非理财）
EQUITY_WEALTH_KEYWORDS = ("指数", "增强", "混合", "股票", "沪深300", "ETF联接")

# 类型信用风险系数（违约概率权重：0=无违约风险，1=高违约风险）
CREDIT_FACTORS = {
    "特别国债": 0.05,  # 政府信用，几乎零违约
    "货币": 0.1,  # 底层存款/短融，风险极低
    "公募固收": 0.5,  # 利率债+高等级信用债
    "债券基金": 0.6,
    "债券": 0.6,  # 企业债/城投债，视资质
    "高端理财": 0.7,  # 净值化，底层多为非标/信用债
    "券商理财": 0.7,
    "理财": 0.8,  # 净值化，底层信用债+非标，信用风险最高
}


def _compute_portfolio_risk(portfolio) -> dict:
    """
    基于投资组合真实数据计算风险评分、等级与五维雷达指标。

    维度（0-100，越大风险越高）：
    - 市场风险：权益类资产占比（美股+港股+基金+ETF+美元/港元基金）
    - 集中度风险：赫芬达尔指数 HHI = Σ(各类型占比²)（衡量整体分散度）
    - 流动性风险：100 - 加权流动性得分（按类型变现速度系数加权）
    - 信用风险：加权违约概率（按类型信用系数加权）
    - 操作风险：持仓数量分段映射（越分散管理越复杂）
    """
    total = float(portfolio.total_value)
    if total <= 0:
        return {
            "risk_score": 0,
            "risk_level": "无数据",
            "dimensions": {"market": 0, "concentration": 0, "liquidity": 0, "credit": 0, "operational": 0},
            "warnings": [],
            "suggestions": [],
        }

    type_dist = portfolio.get_type_distribution()

    def type_ratio(names: list[str]) -> float:
        return sum(float(type_dist.get(n, {}).get("total_value", Decimal("0"))) for n in names) / total * 100

    usd_ratio = type_ratio(["美股", "美元基金（美元）", "QDII"])
    hkd_ratio = type_ratio(["港股", "现金（港元）", "股息基金（港元）"])
    cash_ratio = type_ratio(["货币", "现金", "现金（港元）"])
    bond_ratio = type_ratio(["债券", "债券基金", "公募固收", "特别国债"])
    wealth_ratio = type_ratio(["理财", "高端理财", "券商理财"])

    # 权益类占比（市场风险：股票/基金/ETF 波动敞口）
    equity_ratio = type_ratio(["美股", "港股", "基金", "ETF", "美元基金（美元）", "股息基金（港元）", "QDII"])

    # 券商渠道权益型基金（指数增强/混合等公募基金，按资产性质归入基金而非理财）
    equity_wealth = sum(
        float(p.current_amount or p.initial_amount or 0)
        for p in portfolio.products
        if p.investment_type.value == "券商理财"
        and any(kw in p.name for kw in EQUITY_WEALTH_KEYWORDS)
    )
    equity_ratio += equity_wealth / total * 100

    # 主动管理类占比（操作风险：需盯盘/调仓的资产，理财/债券/固收放着不动）
    active_ratio = type_ratio(
        ["基金", "ETF", "美股", "港股", "美元基金（美元）", "股息基金（港元）", "QDII", "定投基金", "黄金"]
    )
    active_ratio += equity_wealth / total * 100

    # 集中度：赫芬达尔指数 HHI = Σ(占比²)（占比为 0-100 的百分比）
    hhi = sum(
        (float(type_dist.get(name, {}).get("total_value", Decimal("0"))) / total * 100) ** 2
        for name in type_dist
    ) / 100  # 归一化到 0-100 分

    # 最大类型占比（集中度警告用）
    max_type = ""
    max_type_ratio = 0.0
    for name, stats in type_dist.items():
        ratio = float(stats.get("total_value", Decimal("0"))) / total * 100
        if ratio > max_type_ratio:
            max_type_ratio = ratio
            max_type = name

    # 加权流动性得分（按类型变现速度系数）
    liquid_score = sum(
        float(type_dist.get(name, {}).get("total_value", Decimal("0"))) * LIQUIDITY_FACTORS.get(name, 0.5)
        for name in type_dist
    ) / total * 100

    # 加权信用风险得分（按类型违约概率权重，扣除券商渠道权益型基金——非信用资产）
    credit_score = (
        sum(
            float(type_dist.get(name, {}).get("total_value", Decimal("0"))) * CREDIT_FACTORS.get(name, 0.0)
            for name in type_dist
        )
        - equity_wealth * CREDIT_FACTORS.get("券商理财", 0.0)
    ) / total * 100

    product_count = len(portfolio.products)

    dimensions = {
        "market": round(min(100, equity_ratio)),
        "concentration": round(min(100, hhi)),
        "liquidity": round(min(100, max(0, 100 - liquid_score))),
        "credit": round(min(100, credit_score)),
        "operational": round(min(100, active_ratio)),
    }

    risk_score = round(sum(dimensions.values()) / 5)
    if risk_score >= 75:
        risk_level = "高风险"
    elif risk_score >= 60:
        risk_level = "中高风险"
    elif risk_score >= 40:
        risk_level = "中等风险"
    elif risk_score >= 25:
        risk_level = "中低风险"
    else:
        risk_level = "低风险"

    warnings = []
    suggestions = []
    if max_type_ratio > 30:
        warnings.append(f"类型集中度偏高：{max_type} 占比 {max_type_ratio:.0f}%")
        suggestions.append("适当分散投资类型，避免单一品类集中度过高")
    if cash_ratio < 10:
        warnings.append(f"现金及货币类占比偏低（{cash_ratio:.1f}%），流动性储备不足")
        suggestions.append("建议保留 3-6 个月支出的应急资金（现金/货币基金）")
    if usd_ratio + hkd_ratio > 20:
        warnings.append(f"跨境/汇率敞口偏高（{(usd_ratio + hkd_ratio):.0f}%），受汇率波动影响较大")
        suggestions.append("关注美元/港币汇率波动，必要时评估对冲或换汇时机")
    if bond_ratio + wealth_ratio > 60:
        warnings.append(f"固收及理财类占比偏高（{(bond_ratio + wealth_ratio):.0f}%），进攻性不足")
        suggestions.append("评估在风险承受范围内增加权益类资产配置")

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "dimensions": dimensions,
        "total_position": round(total, 2),
        "product_count": product_count,
        "warnings": warnings,
        "suggestions": suggestions,
    }


@router.get("/summary")
async def get_risk_summary():
    """获取风险摘要（基于个人投资组合真实数据）"""
    # Demo 模式下返回模拟风险数据
    if DEMO_MODE:
        from ..demo_data import get_demo_risk_summary

        return get_demo_risk_summary()

    try:
        from .portfolio import _load_portfolio_with_returns

        portfolio = _load_portfolio_with_returns()
        return _compute_portfolio_risk(portfolio)
    except (ValueError, KeyError, TypeError, OSError, RuntimeError) as e:
        return {"error": str(e)}
