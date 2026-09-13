"""
Trend Routes - 净值走势 API

基于资产汇总表（周度记录）绘制总资产与分类账户的净值曲线，
并与沪深300 / 标普500 / 黄金GLD 等基准做归一化对比（起点=100）。
"""

import os
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/trend", tags=["trend"])

DEMO_MODE = os.getenv("ASSET_LENS_DEMO_MODE", "").lower() in ("true", "1", "yes")

# 主要账户（其余银行合并为"其他"，负债类单独归组）
MAIN_ACCOUNTS = ("支付宝", "招商", "富途", "港招", "中金财富", "微信")
OTHER_ACCOUNTS = ("交通", "浦发", "建设", "中信", "民生", "工商", "中银")
DEBT_ACCOUNTS = ("信用卡", "京东白条", "抖音月付", "多多后付", "美团月付")

# 基准列（归一化对比）
BENCHMARK_COLUMNS = {
    "沪深300": "沪深300",
    "标普500": "标普500",
    "黄金GLD": "黄金GLD",
}


def _load_summary_csv() -> list[dict]:
    import csv as csv_module

    from ...config import config

    data_dir = config.get_latest_data_dir()
    if not data_dir or not data_dir.is_dir():
        return []
    files = sorted(Path(data_dir).glob("资产汇总*.csv"))
    if not files:
        return []
    try:
        with open(files[0], encoding="utf-8-sig") as f:
            return list(csv_module.DictReader(f))
    except OSError:
        return []


def _to_float(v) -> float:
    s = (v or "").strip().replace(",", "").replace("%", "")
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def _max_drawdown(series: list[float]) -> float:
    """最大回撤（百分比，正数表示回撤幅度）"""
    if not series:
        return 0.0
    peak = series[0]
    max_dd = 0.0
    for v in series:
        if v > peak:
            peak = v
        if peak > 0:
            dd = (peak - v) / peak
            if dd > max_dd:
                max_dd = dd
    return round(max_dd * 100, 2)


@router.get("/overview")
async def trend_overview():
    """净值走势：总资产、账户结构、基准归一化对比"""
    if DEMO_MODE:
        from ..demo_data import get_demo_trend_overview

        return get_demo_trend_overview()

    rows = _load_summary_csv()
    if not rows:
        return {"dates": [], "total": [], "accounts": {}, "benchmarks": {}, "summary": None}

    dates = [r.get("日期", "").strip() for r in rows]
    total = [_to_float(r.get("总金额")) / 10000 for r in rows]

    # 账户序列（万元）
    accounts: dict[str, list[float]] = {}
    for name in MAIN_ACCOUNTS:
        accounts[name] = [_to_float(r.get(name)) / 10000 for r in rows]
    other = [_to_float(r.get(n)) for r in rows for n in OTHER_ACCOUNTS]
    accounts["其他银行"] = [sum(other[i:: len(rows)]) / 10000 for i in range(len(rows))]
    debt = [_to_float(r.get(n)) for r in rows for n in DEBT_ACCOUNTS]
    accounts["负债（信用卡/白条）"] = [sum(debt[i:: len(rows)]) / 10000 for i in range(len(rows))]

    # 基准归一化：从首条非零记录起 base=100
    benchmarks: dict[str, dict] = {}
    for label, col in BENCHMARK_COLUMNS.items():
        raw = [_to_float(r.get(col)) for r in rows]
        start = next((i for i, v in enumerate(raw) if v > 0), None)
        if start is None or start >= len(raw) - 1:
            continue
        base = raw[start]
        normalized = [round(v / base * 100, 2) if v > 0 else None for v in raw[start:]]
        benchmarks[label] = {
            "start_index": start,
            "start_date": dates[start],
            "raw": [round(v, 2) for v in raw[start:]],
            "normalized": normalized,
            "change": round((raw[-1] / base - 1) * 100, 2),
        }

    # 汇总指标
    start_v, end_v = total[0], total[-1]
    weeks = max(len(rows) - 1, 1)
    growth = (end_v / start_v - 1) * 100 if start_v else 0.0
    annualized = ((end_v / start_v) ** (52 / weeks) - 1) * 100 if start_v > 0 and end_v > 0 else 0.0
    summary = {
        "start_date": dates[0],
        "end_date": dates[-1],
        "start_amount": round(start_v * 10000, 2),
        "end_amount": round(end_v * 10000, 2),
        "growth": round(growth, 2),
        "annualized": round(annualized, 2),
        "weeks": weeks,
        "max_drawdown": _max_drawdown(total),
    }

    return {
        "dates": dates,
        "total": total,
        "accounts": accounts,
        "benchmarks": benchmarks,
        "summary": summary,
    }
