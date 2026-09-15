"""
Equity Routes - 权益类资产（基金/ETF/QDII/美股）风险透视 API

覆盖投资产品 CSV 中"基金/定投基金/ETF/美元基金（美元）/股息基金（港元）/
券商理财（权益型基金）/美股"类产品，按资产类别、风险等级、收益分布透视。
基金/美股收益率为持有期收益率（含未实现浮动），与理财"年化"口径不同。
"""

import os
from contextlib import suppress

from fastapi import APIRouter

router = APIRouter(prefix="/api/equity", tags=["equity"])

# Demo 模式检测
DEMO_MODE = os.getenv("ASSET_LENS_DEMO_MODE", "").lower() in ("true", "1", "yes")

# 权益类投资类型（波动型权益资产；债券/货币/黄金/理财/养老金不算）
EQUITY_TYPES = ("基金", "定投基金", "ETF", "美元基金（美元）", "股息基金（港元）", "券商理财", "美股")

# 名称含这些 → 货币基金（如美元货币基金），剔除出权益口径
CASH_FUND_KEYWORDS = ("货币",)

# 券商渠道权益型基金关键词（从理财剔除、归入权益）
EQUITY_FUND_KEYWORDS = ("指数", "增强", "混合", "股票", "沪深300", "ETF联接")

# CSV 风险等级基础分（波动评分用）
RISK_LEVEL_BASE = {"低": 15, "中低": 30, "中": 55, "中高": 80, "高": 95}

# 资产汇总表里可用的市场基准列
BENCHMARK_COLUMNS = ("沪深300", "中证500", "纳指100", "标普500", "上证指数", "黄金GLD", "能源XLE")


def _pick_benchmark(name: str, category: str) -> str | None:
    """根据产品名称/类别选择最贴近的市场基准（来自资产汇总表的每周指数记录）"""
    n = name
    if category == "黄金":
        return "黄金GLD"
    if "纳斯达克" in n or "纳指" in n:
        return "纳指100"
    if "标普" in n:
        return "标普500"
    if "中证500" in n:
        return "中证500"
    if "XLE" in n or "能源" in n:
        return "能源XLE"
    if "港股" in n:
        return None  # 资产汇总无恒生基准
    if "沪深300" in n or "中证800" in n or "创业板" in n or "科创" in n or "红利" in n:
        return "沪深300"
    if category == "美股直投":
        return "标普500"
    if category == "主动混合":
        return "沪深300"
    if any(kw in n for kw in ("QDII", "环球", "全球", "亚洲", "美元", "股息", "精选")):
        return "标普500"  # 全球权益近似基准
    return None


def _parse_bench_date(s: str) -> tuple[int, int, int] | None:
    """解析资产汇总日期 2026.09.12 / 2026/9/12 -> (2026,9,12)"""
    for sep in (".", "/", "-"):
        parts = s.split(sep)
        if len(parts) == 3:
            try:
                return (int(parts[0]), int(parts[1]), int(parts[2]))
            except ValueError:
                continue
    return None


def _load_benchmark_series() -> tuple[list[tuple[int, int, int]], dict]:
    """读取资产汇总表全部基准序列（每周一条）。返回 (有序日期列表, {日期: {基准: 值}})"""
    import csv as csv_module
    from pathlib import Path

    from ...config import config

    data_dir = config.get_latest_data_dir()
    if not data_dir or not data_dir.is_dir():
        return [], {}
    files = sorted(Path(data_dir).glob("资产汇总*.csv"))
    if not files:
        return [], {}
    dates: list[tuple[int, int, int]] = []
    series: dict = {}
    try:
        with open(files[0], encoding="utf-8-sig") as f:
            rows = list(csv_module.DictReader(f))
        for r in rows:
            d = _parse_bench_date((r.get("日期") or "").strip())
            if not d:
                continue
            vals = {}
            for col in BENCHMARK_COLUMNS:
                raw = (r.get(col) or "").strip()
                if raw:
                    with suppress(ValueError):
                        vals[col] = float(raw)
            if vals:
                dates.append(d)
                series[d] = vals
    except (OSError, ValueError):
        return [], {}
    return dates, series


def _compute_benchmark(product: dict, dates: list, series: dict) -> dict:
    """计算产品持有期的基准涨跌与超额收益（起点=开始日期后第一条有效记录，终点=最新有效记录）
    要求基准数据能覆盖产品买入日（资产汇总表仅 2024.10 起），否则返回无基准。
    """
    bench = _pick_benchmark(product["name"], product["category"])
    sd = product.get("start_date")
    if bench is None or not dates or not sd:
        return {"benchmark": None, "benchmark_return": None, "excess_return": None}
    # 区间对齐：买入日早于基准最早记录 → 数据不足，不对比
    if sd < dates[0]:
        return {"benchmark": None, "benchmark_return": None, "excess_return": None, "bench_reason": "基准数据不足（2024.10 起）"}

    def _first_valid(seq):
        for d in seq:
            v = series.get(d, {}).get(bench)
            if v:
                return d
        return None

    start_d = _first_valid(d for d in dates if d >= sd)
    if start_d is None:
        return {"benchmark": None, "benchmark_return": None, "excess_return": None}
    end_d = _first_valid(reversed(dates))
    if end_d is None or end_d < start_d:
        return {"benchmark": None, "benchmark_return": None, "excess_return": None}

    sv = series[start_d][bench]
    ev = series[end_d][bench]
    bench_ret = (ev / sv - 1) * 100

    # 基准年化（360 天口径，与 make analyze 产品年化一致）：区间涨跌按持有天数折算
    from datetime import date as _date

    interval_days = (_date(*end_d) - _date(*start_d)).days
    bench_annual = ((1 + bench_ret / 100) ** (360 / interval_days) - 1) * 100 if interval_days > 0 else bench_ret

    # 产品年化（make analyze 已算好）；超额 = 年化差（同口径可比）
    annualized = product.get("annualized_return")
    if annualized is None:
        annualized = product["annual_return"]
    excess = annualized - bench_annual
    return {
        "benchmark": bench,
        "benchmark_return": round(bench_ret, 2),          # 区间涨跌（参考）
        "benchmark_annual": round(bench_annual, 2),       # 基准年化（对比用）
        "excess_return": round(excess, 2),                # 年化超额
        "bench_start": f"{start_d[0]}.{start_d[1]:02d}.{start_d[2]:02d}",
        "bench_end": f"{end_d[0]}.{end_d[1]:02d}.{end_d[2]:02d}",
        "bench_interval_days": interval_days,
    }


def _is_equity_product(p) -> bool:
    """是否权益类产品：类型命中且非货币基金"""
    itype = p.investment_type.value
    if itype not in EQUITY_TYPES:
        return False
    if itype == "券商理财" and not any(kw in p.name for kw in EQUITY_FUND_KEYWORDS):
        return False  # 券商理财中的固收类不归权益
    return not any(kw in p.name for kw in CASH_FUND_KEYWORDS)  # 货币基金不归权益


def _classify_asset(name: str, itype: str) -> str:
    """资产类别：美股直投 / 跨境QDII / A股指数 / 主动混合 / 黄金 / 其他"""
    if itype == "美股":
        return "美股直投"
    qdii_kw = ("QDII", "美元", "港元", "股息", "环球", "全球", "纳斯达克", "纳指", "港股")
    if any(kw in name for kw in qdii_kw):
        return "跨境/QDII"
    if "黄金" in name:
        return "黄金"
    if any(kw in name for kw in ("ETF", "指数", "300", "500", "800")):
        return "A股指数"
    if any(kw in name for kw in ("混合", "科技", "精选", "增长")):
        return "主动混合"
    return "其他"


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


def _compute_equity_score(
    name: str, risk_level: str, ret: float, amount: float, total: float, held_days: int | None, category: str
) -> tuple[int, list[str]]:
    """权益波动评分（0-100）：风险等级 + 收益异常（浮亏/高波动）+ 跨境 + 集中 + 时间"""
    reasons: list[str] = []
    score = RISK_LEVEL_BASE.get(risk_level, 55)
    reasons.append(f"风险等级「{risk_level}」基础分 {score}")

    if ret < 0:
        score += 20
        reasons.append(f"收益率 {ret}% 浮亏 +20")
    elif ret >= 15:
        score += 10
        reasons.append(f"收益率 {ret}% 高波动 +10")
    if category == "跨境/QDII":
        score += 5
        reasons.append("跨境/QDII（汇率+市场时差） +5")
    if total > 0 and amount / total >= 0.25:
        score += 10
        reasons.append(f"占权益总额 {amount / total * 100:.0f}% ≥25% 集中 +10")
    if held_days is not None and held_days < 90:
        score += 5
        reasons.append(f"持有 {held_days} 天 <90 天（新买入）+5")
    return min(100, score), reasons


def _generate_advice(products: list[dict]) -> list[dict]:
    """生成调整建议：每个产品都有收益主线建议，叠加风险收益比/新仓/集中维度"""
    advice: list[dict] = []
    total = sum(p.get("amount_cny") or p["amount"] for p in products)

    for p in products:
        ret = p["annual_return"]
        held = p["held_days"] or 0
        amt = p.get("amount_cny") or p["amount"]
        base = {
            "product": p["name"],
            "product_type": p["type"],
            "amount": amt,
        }

        # 1. 收益主线建议（每个产品都命中一条）
        if ret < -10:
            advice.append({**base, "priority": "high", "type": "浮亏观察",
                           "message": f"收益率 {ret}%（持有 {held} 天），浮亏超 10%，评估是补仓摊薄还是止损换仓"})
        elif ret < -3:
            advice.append({**base, "priority": "medium", "type": "浮亏关注",
                           "message": f"收益率 {ret}%（持有 {held} 天），浮亏明显，关注趋势是否反转，可考虑逢低补仓摊薄成本"})
        elif ret < 0:
            advice.append({**base, "priority": "low", "type": "浮亏关注",
                           "message": f"收益率 {ret}%，小幅浮亏，维持持有并关注后续走势"})
        elif ret >= 25:
            advice.append({**base, "priority": "medium", "type": "止盈考虑",
                           "message": f"收益率 {ret}% 已非常可观，建议分批止盈落袋，锁定收益"})
        elif ret >= 15:
            advice.append({**base, "priority": "low", "type": "收益可观",
                           "message": f"收益率 {ret}% 表现良好，可继续持有，回调时考虑部分止盈"})
        elif ret >= 5:
            advice.append({**base, "priority": "low", "type": "持有良好",
                           "message": f"收益率 {ret}% 稳健增长，维持当前持有"})
        else:
            advice.append({**base, "priority": "low", "type": "持有观察",
                           "message": f"收益率 {ret}%，表现平稳，维持持有并关注净值变化"})

        # 2. 风险收益不匹配：高风险等级但收益平庸
        if p["risk_level"] in ("中高", "高") and 0 <= ret < 5:
            advice.append({**base, "priority": "medium", "type": "风险收益比",
                           "message": f"风险等级「{p['risk_level']}」但收益率仅 {ret}%，风险与收益不匹配，可考虑优化持仓结构"})

        # 3. 新仓观察：买入时间短且收益已有明显波动（避免与浮亏建议重复）
        if held < 90 and ret >= 0 and ret > 10:
            advice.append({**base, "priority": "low", "type": "新仓观察",
                           "message": f"新买入 {held} 天，收益率 {ret}% 已有明显波动，先观察再决定加减仓"})

        # 4. 金额集中
        if total > 0 and amt / total >= 0.25:
            advice.append({**base, "priority": "medium", "type": "集中风险",
                           "message": f"单笔占权益总额 {amt / total * 100:.0f}%，持仓集中，建议适当分散"})

        # 5. 基准对比：跑输/跑赢基准（年化口径）
        excess = p.get("excess_return")
        bench = p.get("benchmark")
        if bench and excess is not None:
            if excess <= -5:
                advice.append({**base, "priority": "medium", "type": "跑输基准",
                               "message": f"年化跑输{bench} {abs(excess):.1f} 个百分点（产品年化 {p.get('annualized_return')}% vs 基准年化 {p['benchmark_annual']}%），检视是否仍值得持有"})
            elif excess >= 5:
                advice.append({**base, "priority": "low", "type": "跑赢基准",
                               "message": f"年化跑赢{bench} {excess:.1f} 个百分点（产品年化 {p.get('annualized_return')}% vs 基准年化 {p['benchmark_annual']}%），表现优于市场"})

    priority_order = {"high": 0, "medium": 1, "low": 2}
    advice.sort(key=lambda x: (priority_order.get(x["priority"], 9), -x["amount"]))
    return advice


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


def _load_equity_products() -> list[dict]:
    from .portfolio import _load_portfolio_with_returns

    portfolio = _load_portfolio_with_returns()
    usd_rate, hkd_rate = _load_fx_rates()
    products = []
    for p in portfolio.products:
        if not _is_equity_product(p):
            continue
        amount = float(p.current_amount or p.initial_amount or 0)
        held_days = p.investment_days
        itype = p.investment_type.value
        category = _classify_asset(p.name, itype)
        sd = getattr(p, "start_date", None)
        start_date = (sd.year, sd.month, sd.day) if hasattr(sd, "year") else None
        currency = "USD" if itype in ("美股", "美元基金（美元）") else ("HKD" if itype == "股息基金（港元）" else "CNY")
        fx_rate = usd_rate if currency == "USD" else (hkd_rate if currency == "HKD" else 1.0)
        # 权益主口径 = 持有期收益率（与基准区间涨跌可比）；年化作为参考
        holding_return = float(p.return_rate) if p.return_rate is not None else (float(p.annual_return or 0) if p.annual_return is not None else 0.0)
        annualized = float(p.annual_return or 0) if p.annual_return is not None else None
        products.append(
            {
                "name": p.name,
                "type": itype,
                "category": category,
                "risk_level": p.risk_level.value if p.risk_level else "-",
                "amount": round(amount, 2),
                "amount_cny": round(amount * fx_rate, 2),
                "annual_return": round(holding_return, 2),
                "annualized_return": round(annualized, 2) if annualized is not None else None,
                "held_days": held_days,
                "held_bucket": _held_bucket(held_days),
                "start_date": start_date,
                "currency": currency,
            }
        )

    total = sum(p["amount_cny"] for p in products)
    for p in products:
        score, reasons = _compute_equity_score(
            p["name"], p["risk_level"], p["annual_return"], p["amount_cny"], total, p["held_days"], p["category"]
        )
        p["risk_score"] = score
        p["score_reasons"] = reasons
    products.sort(key=lambda x: (-x["risk_score"], x["annual_return"]))
    return products


@router.get("/overview")
async def equity_overview():
    """权益类资产风险透视汇总"""
    if DEMO_MODE:
        from ..demo_data import get_demo_equity_overview

        return get_demo_equity_overview()

    from .portfolio import _load_portfolio_with_returns

    products = _load_equity_products()
    portfolio = _load_portfolio_with_returns()
    portfolio_total = float(portfolio.total_value)

    if not products or portfolio_total <= 0:
        return {
            "total_amount": 0,
            "ratio": 0,
            "product_count": 0,
            "avg_return": 0,
            "negative_count": 0,
            "negative_products": [],
            "categories": [],
            "risk_distribution": {},
            "held_distribution": {},
            "advice": [],
            "products": [],
        }

    total = sum(p["amount_cny"] for p in products)

    # 资产类别分布
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

    # 风险等级分布
    risk_dist: dict[str, float] = {}
    for p in products:
        risk_dist[p["risk_level"]] = round(risk_dist.get(p["risk_level"], 0.0) + p["amount_cny"], 2)

    # 持有时间分布
    held_dist: dict[str, float] = {}
    for p in products:
        held_dist[p["held_bucket"]] = round(held_dist.get(p["held_bucket"], 0.0) + p["amount_cny"], 2)

    # 收益分布（正/负）
    positive = [p for p in products if p["annual_return"] >= 0]
    negative = [p for p in products if p["annual_return"] < 0]
    avg_return = sum(p["annual_return"] for p in products) / len(products)

    # 基准对比：每个产品算持有期基准涨跌与超额收益
    bench_dates, bench_series = _load_benchmark_series()
    for p in products:
        p.update(_compute_benchmark(p, bench_dates, bench_series))

    # 生成调整建议，并为每个产品挂接详情（含关联建议）
    advice = _generate_advice(products)
    for p in products:
        matched_advice = [
            a for a in advice
            if a["product"] == p["name"] and a.get("product_type") == p["type"]
        ]
        p["detail"] = {
            "name": p["name"],
            "type_desc": f"{p['category']}（{p['type']}）",
            "annualized_return": p.get("annualized_return"),
            "benchmark": p.get("benchmark"),
            "benchmark_return": p.get("benchmark_return"),
            "benchmark_annual": p.get("benchmark_annual"),
            "excess_return": p.get("excess_return"),
            "bench_start": p.get("bench_start"),
            "bench_end": p.get("bench_end"),
            "bench_interval_days": p.get("bench_interval_days"),
            "advice": [{"priority": a["priority"], "type": a["type"], "message": a["message"]} for a in matched_advice],
        }

    # 组合层面观察（与 CLI make analyze 的组合级建议对齐，权益视角）
    portfolio_insights: list[dict] = []

    # 1. 风险结构：中高+高 占比
    high_risk_amount = sum(p["amount_cny"] for p in products if p["risk_level"] in ("中高", "高"))
    high_risk_ratio = high_risk_amount / total * 100 if total > 0 else 0
    if high_risk_ratio > 70:
        portfolio_insights.append({
            "level": "high",
            "type": "风险结构",
            "message": f"权益资产中中高/高风险占比 {high_risk_ratio:.0f}%，整体偏高风险，波动敏感，注意控制仓位",
        })
    elif high_risk_ratio > 50:
        portfolio_insights.append({
            "level": "medium",
            "type": "风险结构",
            "message": f"中高/高风险产品占比 {high_risk_ratio:.0f}%，权益仓位波动较大，建议保留一定现金缓冲",
        })

    # 2. 类别集中度
    if categories:
        top_cat = categories[0]
        if top_cat["ratio"] >= 45:
            portfolio_insights.append({
                "level": "medium",
                "type": "类别集中",
                "message": f"{top_cat['name']}类占比 {top_cat['ratio']:.0f}%，持仓集中度偏高，注意单一市场/风格风险",
            })

    # 3. 浮亏面
    if len(negative) > 0:
        loss_ratio = len(negative) / len(products) * 100
        if loss_ratio >= 30:
            portfolio_insights.append({
                "level": "medium",
                "type": "浮亏面",
                "message": f"{len(negative)}/{len(products)} 个产品浮亏（{loss_ratio:.0f}%），关注整体回撤幅度，避免频繁操作",
            })

    # 4. 整体表现
    avg_return_str = f"{avg_return:.2f}"
    if avg_return >= 5:
        portfolio_insights.append({
            "level": "low",
            "type": "整体表现",
            "message": f"权益组合平均收益 {avg_return_str}%，整体表现良好，维持当前配置",
        })
    elif avg_return < 0:
        portfolio_insights.append({
            "level": "high",
            "type": "整体表现",
            "message": f"权益组合平均收益 {avg_return_str}%，整体浮亏，建议审视持仓结构是否需调整",
        })

    # 5. 外币敞口：美元/港元资产占比
    fx_amount = sum(p["amount_cny"] for p in products if p["currency"] in ("USD", "HKD"))
    fx_ratio = fx_amount / total * 100 if total > 0 else 0
    if fx_ratio >= 40:
        portfolio_insights.append({
            "level": "medium",
            "type": "外币敞口",
            "message": f"美元/港元资产占比 {fx_ratio:.0f}%，汇率波动对组合影响较大，关注美元/港元走势",
        })
    elif fx_ratio >= 15:
        portfolio_insights.append({
            "level": "low",
            "type": "外币敞口",
            "message": f"美元/港元资产占比 {fx_ratio:.0f}%，有一定汇率敞口，收益中已含汇率变动影响",
        })

    return {
        "total_amount": round(total, 2),
        "portfolio_total": round(portfolio_total, 2),
        "ratio": round(total / portfolio_total * 100, 1),
        "product_count": len(products),
        "avg_return": round(avg_return, 2),
        "positive_count": len(positive),
        "negative_count": len(negative),
        "negative_products": negative,
        "categories": categories,
        "risk_distribution": risk_dist,
        "held_distribution": held_dist,
        "portfolio_insights": portfolio_insights,
        "advice": advice,
        "products": products,
    }
