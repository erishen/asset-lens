"""
市场环境指标抓取器。

在 make analyze / CLI analyze 时调用 update_market_env()：
抓取 auto=true 的市场指标（十年国债、沪深300估值、金价），
更新 data/market_env.json（仅覆盖 auto=true 的字段，保留手动维护字段），
供 Web 组合配置页读取。失败时静默回退，不中断分析主流程。
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

MARKET_ENV_FILE = Path(__file__).resolve().parent / "market_env.json"

_ZH_DATE_RE = re.compile(r"(\d{4})年(\d{2})月(\d{2})日")


async def _fetch_bond_yield() -> dict:
    """中债国债收益率曲线（yield.chinabond.com.cn），取 10 年期（每行第 7 个值）。"""
    from asset_lens.web.aiohttp_session import async_get

    url = "https://yield.chinabond.com.cn/cbweb-cbrc-web/cbrc/showCbrc"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://yield.chinabond.com.cn/"}
    async with await async_get(url, headers=headers, timeout=10) as resp:
        html = await resp.text()
    m = re.search(r"1\.\d{4}</td>(?:\s*<td>1\.\d{4}</td>){6}\s*<td>2\.\d{4}</td>", html)
    if not m:
        raise ValueError("bond yield parse failed")
    vals = [float(x) for x in re.findall(r"[12]\.\d{4}", m.group(0))]
    if len(vals) < 7:
        raise ValueError("bond yield too few values")
    return {"value": vals[6], "date": "auto"}


async def _fetch_hs300_valuation() -> dict:
    """value500 沪深300 滚动市盈率与股债利差（m.value500.com）。"""
    from asset_lens.web.aiohttp_session import async_get

    url = "http://m.value500.com/mCSI300.asp"
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"}
    async with await async_get(url, headers=headers, timeout=10) as resp:
        html = await resp.text()
    pe = re.search(r"沪深300指数滚动市盈率</li></div>\s*<div class=\"TL5\">([0-9.]+)", html)
    spread = re.search(r"沪深300指数股债利差</li></div>\s*<div class=\"TL5\">([0-9.]+)", html)
    if not pe or not spread:
        raise ValueError("hs300 valuation parse failed")
    mdate = _ZH_DATE_RE.search(html)
    date = f"{mdate.group(1)}-{mdate.group(2)}-{mdate.group(3)}" if mdate else "auto"
    return {"pe": float(pe.group(1)), "spread": float(spread.group(1)), "date": date}


async def _fetch_gold_price() -> dict:
    """新浪行情 上海黄金交易所黄金T+D（元/克）。"""
    from asset_lens.web.aiohttp_session import async_get

    url = "http://hq.sinajs.cn/list=gds_AUTD"
    headers = {"Referer": "http://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"}
    async with await async_get(url, headers=headers, timeout=10) as resp:
        text = await resp.text()
    payload = text.split('"')[1]
    parts = payload.split(",")
    if len(parts) < 13 or not parts[0]:
        raise ValueError("gold parse failed")
    return {"value": float(parts[0]), "date": parts[12]}


def update_market_env(verbose: bool = False) -> dict:
    """
    抓取 auto=true 的市场指标并更新 market_env.json。

    Returns:
        {"updated": [指标名...], "failed": [指标名...], "updated_at": "YYYY-MM-DD"}
    """
    try:
        with open(MARKET_ENV_FILE, encoding="utf-8") as f:
            env = json.load(f)
    except (OSError, ValueError) as e:
        logger.warning("market_env.json 读取失败: %s", e)
        return {"updated": [], "failed": ["config"], "updated_at": ""}

    ind = env.get("indicators", {})
    auto_keys = [k for k, v in ind.items() if v.get("auto")]

    async def _run():
        results = {}
        if "cn_10y_bond_yield" in auto_keys:
            try:
                results["cn_10y_bond_yield"] = await _fetch_bond_yield()
            except Exception as e:
                logger.debug("bond yield fetch failed: %s", e)
        if "hs300_pe" in auto_keys or "equity_bond_spread" in auto_keys:
            try:
                r = await _fetch_hs300_valuation()
                results["hs300_pe"] = {"value": r["pe"], "date": r["date"]}
                results["equity_bond_spread"] = {"value": r["spread"], "date": r["date"]}
            except Exception as e:
                logger.debug("hs300 valuation fetch failed: %s", e)
        if "gold_price_cny_g" in auto_keys:
            try:
                results["gold_price_cny_g"] = await _fetch_gold_price()
            except Exception as e:
                logger.debug("gold fetch failed: %s", e)
        return results

    try:
        results = asyncio.run(_run())
    except Exception as e:
        logger.warning("市场指标抓取整体失败: %s", e)
        return {"updated": [], "failed": auto_keys, "updated_at": ""}
    finally:
        try:
            from asset_lens.web.aiohttp_session import close_session

            asyncio.run(close_session())
        except Exception:
            pass

    updated = []
    failed = []
    for key in auto_keys:
        if key in results:
            try:
                ind[key]["value"] = float(results[key]["value"])
                if results[key].get("date") and results[key]["date"] != "auto":
                    ind[key]["source"] = f"{ind[key].get('source', '').split('（')[0]}（{results[key]['date']} 自动抓取）"
                updated.append(key)
            except (TypeError, ValueError) as e:
                logger.warning("指标 %s 写入失败: %s", key, e)
                failed.append(key)
        else:
            failed.append(key)

    if updated:
        today = datetime.now().strftime("%Y-%m-%d")
        env["data_date"] = today
        env["updated_at"] = today
        try:
            with open(MARKET_ENV_FILE, "w", encoding="utf-8") as f:
                json.dump(env, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.warning("market_env.json 写入失败: %s", e)
            return {"updated": [], "failed": auto_keys, "updated_at": ""}

    if verbose:
        print(f"📈 市场环境指标更新: 成功 {len(updated)} 个, 失败 {len(failed)} 个")
        for k in updated:
            print(f"   ✓ {k} = {ind[k]['value']}")
        for k in failed:
            print(f"   ✗ {k}（保留原值）")

    return {"updated": updated, "failed": failed, "updated_at": env.get("updated_at", "")}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(update_market_env(verbose=True))
