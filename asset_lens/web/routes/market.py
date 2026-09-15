"""
Market Routes - 市场数据相关 API
"""

import logging
import os

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market", tags=["market"])

# Demo 模式检测
DEMO_MODE = os.getenv("ASSET_LENS_DEMO_MODE", "").lower() in ("true", "1", "yes")


class MarketIndex(BaseModel):
    """市场指数模型"""

    code: str
    name: str
    price: float = 0
    change: float = 0
    change_percent: float = 0


@router.get("/indexes", response_model=list[MarketIndex])
async def get_market_indexes():
    """获取市场主要指数"""
    # Demo 模式下返回模拟数据
    if DEMO_MODE:
        from ..demo_data import get_demo_market_indexes

        return [MarketIndex(**idx) for idx in get_demo_market_indexes()]

    indexes = await _get_market_indexes()
    return indexes


async def _get_market_indexes() -> list[MarketIndex]:
    """获取市场指数数据"""
    from ..aiohttp_session import async_get

    index_codes = [
        ("sh000001", "上证指数"),
        ("sh000300", "沪深300"),
        ("sh000016", "上证50"),
        ("sh000905", "中证500"),
        ("sz399001", "深证成指"),
        ("sz399006", "创业板指"),
    ]

    codes_str = ",".join([code for code, _ in index_codes])
    url = f"http://hq.sinajs.cn/list={codes_str}"
    headers = {
        "Referer": "http://finance.sina.com.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    try:
        async with await async_get(url, headers=headers, timeout=10) as response:
            if response.status == 200:
                result = []
                content = await response.text()

                for code, name in index_codes:
                    pattern = f'var hq_str_{code}="'
                    start = content.find(pattern)

                    if start != -1:
                        start += len(pattern)
                        end = content.find('";', start)
                        data_str = content[start:end]

                        if data_str:
                            parts = data_str.split(",")
                            if len(parts) >= 32:
                                current_price = float(parts[3]) if parts[3] else 0
                                prev_close = float(parts[2]) if parts[2] else 0
                                change = current_price - prev_close if prev_close > 0 else 0
                                change_percent = (change / prev_close * 100) if prev_close > 0 else 0

                                result.append(
                                    MarketIndex(
                                        code=code,
                                        name=name,
                                        price=current_price,
                                        change=change,
                                        change_percent=change_percent,
                                    )
                                )

                return result

    except (ConnectionError, TimeoutError, ValueError, KeyError, OSError) as e:
        logger.debug(f"忽略异常: {e}")

    return []


@router.get("/hot-stocks")
async def get_hot_stocks(
    market: str = Query("all", description="市场: all/sh/sz"),
    limit: int = Query(10, description="返回数量"),
):
    """
    获取热门股票

    Args:
        market: 市场 (all/sh/sz)
        limit: 返回数量
    """
    from ...data.market_stock_fetcher import market_stock_fetcher

    try:
        stocks = market_stock_fetcher.fetch_all_cn_stocks(max_pages=1)
        return {"market": market, "count": len(stocks[:limit]), "stocks": stocks[:limit]}
    except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/north-flow")
async def get_north_flow():
    try:
        flow_data = await _get_north_flow_data()
        return flow_data
    except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _get_north_flow_data() -> dict:
    from ..aiohttp_session import async_get

    url = "http://push2.eastmoney.com/api/qt/stock/fflow/kline/get"
    params = {
        "lmt": "0",
        "klt": "1",
        "secid": "1.000001",
        "fields1": "f1,f2,f3,f7",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63",
    }

    try:
        async with await async_get(url, params=params, timeout=10) as response:
            if response.status == 200:
                data = await response.json(content_type=None)

                if data.get("data") and data["data"].get("klines"):
                    klines = data["data"]["klines"]

                    if klines:
                        latest = klines[-1].split(",")
                        return {
                            "date": latest[0],
                            "main_inflow": float(latest[1]) if len(latest) > 1 else 0,
                            "retail_inflow": float(latest[5]) if len(latest) > 5 else 0,
                            "total_inflow": float(latest[9]) if len(latest) > 9 else 0,
                        }

    except (ValueError, TypeError) as e:
        logger.debug("市场数据参数解析失败: %s", e)

    return {"date": "", "main_inflow": 0, "retail_inflow": 0, "total_inflow": 0}


@router.get("/sentiment")
async def get_market_sentiment():
    import asyncio

    from ...core.market_sentiment import MarketSentimentAnalyzer

    try:
        analyzer = MarketSentimentAnalyzer()
        sentiment = await asyncio.to_thread(analyzer.analyze)

        return {
            "overall_score": sentiment.overall_score,
            "trend": sentiment.trend,
            "risk_level": sentiment.risk_level,
            "indicators": [
                {
                    "name": i.name,
                    "score": i.value,
                    "level": i.level,
                    "description": i.description,
                }
                for i in sentiment.indicators
            ],
            "suggestions": sentiment.suggestions,
            "analysis_time": sentiment.analysis_time,
        }
    except (ValueError, KeyError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ---------------------------------------------------------------------------
# 资产配置动态参考区间（基于市场环境推导）
# ---------------------------------------------------------------------------

import json as _json
from pathlib import Path as _Path

_MARKET_ENV_FILE = _Path(__file__).resolve().parent.parent.parent / "data" / "market_env.json"

# ---------------------------------------------------------------------------
# 市场指标自动抓取（半自动：auto=true 的指标实时拉取，失败回退配置文件）
# ---------------------------------------------------------------------------

import re as _re

_ZH_DATE_RE = _re.compile(r'(\d{4})年(\d{2})月(\d{2})日')


async def _fetch_bond_yield():
    """中债国债收益率曲线（yield.chinabond.com.cn），取 10 年期（每行第 7 个值）。"""
    from ..aiohttp_session import async_get
    url = "https://yield.chinabond.com.cn/cbweb-cbrc-web/cbrc/showCbrc"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://yield.chinabond.com.cn/"}
    async with await async_get(url, headers=headers, timeout=10) as resp:
        html = await resp.text()
    # 第一组（中债国债收益率曲线）8 个值：3月6月1年3年5年7年10年30年
    m = _re.search(r'1\.\d{4}</td>(?:\s*<td>1\.\d{4}</td>){6}\s*<td>2\.\d{4}</td>', html)
    if not m:
        raise ValueError("bond yield parse failed")
    vals = [float(x) for x in _re.findall(r'[12]\.\d{4}', m.group(0))]
    if len(vals) < 7:
        raise ValueError("bond yield too few values")
    return {"value": vals[6], "date": "auto"}


async def _fetch_hs300_valuation():
    """value500 沪深300 滚动市盈率与股债利差（m.value500.com）。"""
    from ..aiohttp_session import async_get
    url = "http://m.value500.com/mCSI300.asp"
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"}
    async with await async_get(url, headers=headers, timeout=10) as resp:
        html = await resp.text()
    pe = _re.search(r'沪深300指数滚动市盈率</li></div>\s*<div class="TL5">([0-9.]+)', html)
    spread = _re.search(r'沪深300指数股债利差</li></div>\s*<div class="TL5">([0-9.]+)', html)
    if not pe or not spread:
        raise ValueError("hs300 valuation parse failed")
    mdate = _ZH_DATE_RE.search(html)
    date = f"{mdate.group(1)}-{mdate.group(2)}-{mdate.group(3)}" if mdate else "auto"
    return {"pe": float(pe.group(1)), "spread": float(spread.group(1)), "date": date}


async def _fetch_gold_price():
    """新浪行情 上海黄金交易所黄金T+D（元/克）。"""
    from ..aiohttp_session import async_get
    url = "http://hq.sinajs.cn/list=gds_AUTD"
    headers = {"Referer": "http://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"}
    async with await async_get(url, headers=headers, timeout=10) as resp:
        text = await resp.text()
    payload = text.split('"')[1]
    parts = payload.split(",")
    if len(parts) < 13 or not parts[0]:
        raise ValueError("gold parse failed")
    return {"value": float(parts[0]), "date": parts[12]}




@router.get("/advice")
async def get_allocation_advice():
    """
    基于 market_env.json 中的市场指标，推导各资产大类的参考配置区间及理由。
    供组合配置页展示；数据需随市场变化在 market_env.json 中更新。
    """
    env = {}
    try:
        with open(_MARKET_ENV_FILE, encoding="utf-8") as f:
            env = _json.load(f)
    except (OSError, ValueError) as e:
        logger.warning("market_env.json 读取失败: %s", e)

    ind = env.get("indicators", {})
    data_date = env.get("data_date", "未知")

    # 文件新鲜（analyze 最近 7 天内更新过）则直接读文件；否则实时抓取兜底
    fresh = False
    upd = env.get("updated_at") or env.get("data_date")
    try:
        from datetime import datetime as _dt
        if upd:
            fresh = (_dt.now() - _dt.strptime(upd, "%Y-%m-%d")).days <= 7
    except (ValueError, TypeError):
        fresh = False

    # 实时抓取 auto=true 的指标（失败回退配置文件值）
    live = {}
    auto_keys = [k for k, v in ind.items() if v.get("auto")]
    if not fresh:
        try:
            if "cn_10y_bond_yield" in auto_keys:
                try:
                    r = await _fetch_bond_yield()
                    live["cn_10y_bond_yield"] = r
                except Exception as e:
                    logger.debug("bond yield fetch failed: %s", e)
            if "hs300_pe" in auto_keys or "equity_bond_spread" in auto_keys:
                try:
                    r = await _fetch_hs300_valuation()
                    live["hs300_pe"] = {"value": r["pe"], "date": r["date"]}
                    live["equity_bond_spread"] = {"value": r["spread"], "date": r["date"]}
                except Exception as e:
                    logger.debug("hs300 valuation fetch failed: %s", e)
            if "gold_price_cny_g" in auto_keys:
                try:
                    r = await _fetch_gold_price()
                    live["gold_price_cny_g"] = r
                except Exception as e:
                    logger.debug("gold fetch failed: %s", e)
        except Exception as e:
            logger.debug("market auto fetch skipped: %s", e)

    def num(key):
        try:
            if key in live and live[key].get("value") is not None:
                return float(live[key]["value"])
            v = ind.get(key, {}).get("value")
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    bond = num("cn_10y_bond_yield")
    spread = num("equity_bond_spread")
    pe = num("hs300_pe")
    gold = num("gold_price_cny_g")
    money = num("money_fund_yield")
    wealth = num("wealth_avg_yield")

    cats = []

    # 权益类：以股债利差为主信号，PE 分位为约束
    eq_adj = 0
    eq_reasons = []
    if spread is not None:
        if spread >= 5:
            eq_adj += 5
            eq_reasons.append(f"股债利差{spread:.2f}%处于历史极值区域（≥5%），权益相对债券性价比高")
        elif spread <= 3:
            eq_adj -= 5
            eq_reasons.append(f"股债利差{spread:.2f}%偏低（≤3%），权益相对债券吸引力不足")
    if pe is not None:
        if pe < 12:
            eq_adj += 3
            eq_reasons.append(f"沪深300 PE {pe:.1f} 低于12，估值偏低")
        elif pe > 15:
            eq_adj -= 3
            eq_reasons.append(f"沪深300 PE {pe:.1f} 高于15，估值偏高")
    eq_min, eq_max = 15 + eq_adj, 30 + eq_adj
    cats.append({"name": "权益类", "min": eq_min, "max": eq_max,
                 "reason": "；".join(eq_reasons) if eq_reasons else "市场信号中性，维持基准区间"})

    # 固收类：以十年国债收益率为主
    fi_adj = 0
    fi_reasons = []
    if bond is not None:
        if bond >= 3:
            fi_adj += 5
            fi_reasons.append(f"10年期国债收益率{bond:.2f}%较高（≥3%），债券配置价值提升")
        elif bond < 2:
            fi_adj -= 5
            fi_reasons.append(f"10年期国债收益率{bond:.2f}%处于历史低位（<2%），纯债预期回报偏低")
    fi_min, fi_max = 25 + fi_adj, 45 + fi_adj
    cats.append({"name": "固收类", "min": fi_min, "max": fi_max,
                 "reason": "；".join(fi_reasons) if fi_reasons else "市场信号中性，维持基准区间"})

    # 理财类：理财收益相对国债的超额
    we_adj = 0
    we_reasons = []
    if wealth is not None and bond is not None:
        prem = wealth - bond
        if prem >= 0.8:
            we_adj += 5
            we_reasons.append(f"理财平均年化{wealth:.2f}%较十年国债高出{prem:.2f}pp（≥0.8pp），固收增强价值高")
        elif prem < 0.3:
            we_adj -= 5
            we_reasons.append(f"理财相对国债超额仅{prem:.2f}pp（<0.3pp），性价比下降")
        else:
            we_reasons.append(f"理财平均年化{wealth:.2f}%较十年国债高出约{prem:.2f}pp，仍具固收增强配置价值")
    we_min, we_max = 20 + we_adj, 35 + we_adj
    cats.append({"name": "理财类", "min": we_min, "max": we_max,
                 "reason": "；".join(we_reasons) if we_reasons else "市场信号中性，维持基准区间"})

    # 现金类：货币基金收益低则减少持有
    ca_adj = 0
    ca_reasons = []
    if money is not None:
        if money >= 2.5:
            ca_adj += 5
            ca_reasons.append(f"货币基金7日年化{money:.2f}%较高（≥2.5%），现金回报可观")
        elif money < 1.5:
            ca_adj -= 5
            ca_reasons.append(f"货币基金7日年化仅约{money:.2f}%（<1.5%），现金机会成本高，仅保留流动性需求")
    ca_min, ca_max = max(0, 5 + ca_adj), max(5, 15 + ca_adj)
    cats.append({"name": "现金储备", "min": ca_min, "max": ca_max,
                 "reason": "；".join(ca_reasons) if ca_reasons else "市场信号中性，维持基准区间"})

    # 黄金：历史高位区收窄并提示谨慎
    if gold is not None and gold >= 850:
        gold_min, gold_max = 3, 8
        gold_reason = f"金价约{gold:.0f}元/克处于历史高位区（≥850），近期波动加大，建议控制比例、不宜追高"
    else:
        gold_min, gold_max = 5, 10
        gold_reason = "金价未处历史高位区，维持常规配置区间"
    cats.append({"name": "黄金", "min": gold_min, "max": gold_max, "reason": gold_reason})

    # 养老：与市场环境相关性低
    cats.append({"name": "养老储备", "min": 0, "max": 10,
                 "reason": "养老储备为长期资金，与市场环境相关性低，按个人养老规划设定"})

    def _status(key):
        if key in live:
            d = live[key].get("date", "")
            return f"实时抓取 {d}" if d and d != "auto" else "实时抓取"
        if fresh and ind.get(key, {}).get("auto"):
            return f"自动更新 {env.get('updated_at', '')}"
        return "配置值（手动更新）"

    indicators = [
        {"name": "10年期国债收益率", "value": f"{bond:.2f}%" if bond is not None else "-",
         "source": ind.get("cn_10y_bond_yield", {}).get("source", ""), "impact": "固收类",
         "status": _status("cn_10y_bond_yield")},
        {"name": "沪深300 PE(TTM)", "value": f"{pe:.2f}" if pe is not None else "-",
         "source": ind.get("hs300_pe", {}).get("source", ""), "impact": "权益类",
         "status": _status("hs300_pe")},
        {"name": "沪深300股债利差", "value": f"{spread:.2f}%" if spread is not None else "-",
         "source": ind.get("equity_bond_spread", {}).get("source", ""), "impact": "权益类",
         "status": _status("equity_bond_spread")},
        {"name": "银行理财平均年化", "value": f"{wealth:.2f}%" if wealth is not None else "-",
         "source": ind.get("wealth_avg_yield", {}).get("source", ""), "impact": "理财类",
         "status": _status("wealth_avg_yield")},
        {"name": "货币基金7日年化", "value": f"{money:.2f}%" if money is not None else "-",
         "source": ind.get("money_fund_yield", {}).get("source", ""), "impact": "现金",
         "status": _status("money_fund_yield")},
        {"name": "黄金价格(Au9999)", "value": f"{gold:.0f}元/克" if gold is not None else "-",
         "source": ind.get("gold_price_cny_g", {}).get("source", ""), "impact": "黄金",
         "status": _status("gold_price_cny_g")},
    ]

    # 投资组合数据来源（与 make analyze 同目录口径）
    portfolio_source = {}
    try:
        from ...config import config as _config

        _dir = _config.get_latest_data_dir()
        if _dir is not None and _dir.is_dir():
            name = _dir.name
            as_of = ""
            m = _re.search(r"(\d{8})", name)
            if m:
                d = m.group(1)
                as_of = f"{d[:4]}-{d[4:6]}-{d[6:]}"
            portfolio_source = {"dir": name, "as_of": as_of}
    except Exception as e:
        logger.debug("portfolio source resolve failed: %s", e)

    return {
        "data_date": data_date,
        "updated_at": env.get("updated_at", ""),
        "mode": "live_fetch" if not fresh else "file_snapshot",
        "source_file": "asset_lens/data/market_env.json",
        "portfolio_source": portfolio_source,
        "categories": cats,
        "indicators": indicators,
        "note": "参考区间基于公开市场数据动态推导（非投资建议）；auto 指标在 make analyze 时自动更新（每周），超 7 天未更新则页面实时抓取兜底；标『配置值』的需按 source 提示手动维护。"
    }
