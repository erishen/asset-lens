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
import os
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


def _fetch_fed_funds_rate_via_cmd(cmd: str) -> dict:
    """跑 FED_FETCH_CMD（外部兜底抓取命令），从其 stdout 末行读 JSON。

    背景：FRED（Akamai）按 TLS 指纹拦截 curl/urllib 类客户端（换代理节点无效，
    表现为连接重置/读超时），只有浏览器指纹能通过。本仓（public）不耦合浏览器
    依赖，故暴露 env 钩子：部署方（如 resolve-studio 容器 compose）可注入一条
    「走 CDP 浏览器抓取 FRED」的命令。约定：stdout 最后一行为
    {"value": <float>, "date": "YYYY-MM-DD"} 的 JSON 对象，退出码非 0 视为失败。
    """
    import json as _json
    import subprocess

    proc = subprocess.run(
        ["sh", "-c", cmd],
        capture_output=True,
        text=True,
        timeout=150,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"FED_FETCH_CMD rc={proc.returncode}: {proc.stderr.strip()[:150]}"
        )
    last_json = None
    for line in reversed(proc.stdout.strip().splitlines()):
        s = line.strip()
        if s.startswith("{"):
            last_json = s
            break
    if not last_json:
        raise ValueError("FED_FETCH_CMD produced no JSON object on stdout")
    data = _json.loads(last_json)
    return {"value": float(data["value"]), "date": str(data.get("date", ""))}


def _fetch_fed_funds_rate_sync(proxy: str | None) -> dict:
    """同步抓取 FRED 联邦基金利率（urllib，标准库，线程池里调用）。"""
    import urllib.request

    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FF&cosd=2025-01-01"
    handlers = (
        [urllib.request.ProxyHandler({"https": proxy, "http": proxy})]
        if proxy
        else []
    )
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with opener.open(req, timeout=30) as r:
        text = r.read().decode("utf-8", "replace")
    last_val = None
    last_date = ""
    for line in reversed(text.strip().splitlines()):
        parts = line.split(",")
        if len(parts) < 2 or parts[0] == "observation_date":
            continue
        v = parts[1].strip()
        if v in ("", "."):
            continue
        try:
            last_val = float(v)
            last_date = parts[0]
            break
        except ValueError:
            continue
    if last_val is None:
        raise ValueError("FF rate parse failed (no valid observation)")
    return {"value": last_val, "date": last_date}


async def _fetch_fed_funds_rate(proxy: str | None = None) -> dict:
    """FRED 联邦基金利率目标值（序列 FF，FOMC 决议后的目标区间中值，与 CSV
    手工列「美联基利率」同源可比）。

    FRED 免 API key 公开 CSV 端点，美国源，CN 直连不可达 → 必须走代理。
    数据在议息会议后更新，两次议息之间值不变属正常。取值：序列最后一个非缺失观测值。

    实现说明：
    1) 主路径 urllib（同步，经 asyncio.to_thread 在线程池执行）——比 aiohttp 稳
       （本环境实测 aiohttp 的 per-request/session 级 proxy 在 3.14 下 60s 超时）。
    2) FRED（Akamai）会按 TLS 指纹拦截 curl/urllib 这类非浏览器客户端，换代理
       节点无效；此时若部署方配置了 FED_FETCH_CMD（一条走 CDP 浏览器指纹的外部
       抓取命令），自动降级到它。未配置该 env 时行为不变（仅 urllib）。
    """
    import asyncio

    cmd = os.getenv("FED_FETCH_CMD", "").strip()
    try:
        return await asyncio.to_thread(_fetch_fed_funds_rate_sync, proxy)
    except Exception as e:
        if cmd:
            logger.info("fed urllib 抓取失败（%s: %s），改用 FED_FETCH_CMD", type(e).__name__, str(e)[:80])
            return await asyncio.to_thread(_fetch_fed_funds_rate_via_cmd, cmd)
        raise


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
        if "fed_funds_rate" in auto_keys:
            # FRED 是美国源，必须走代理；宿主/容器代理地址由 env 提供
            # （asset-lens Makefile 会把 HTTP_PROXY_VALUE 导出为 HTTPS_PROXY；
            #  容器内 PSE 注入 WP_PROXY 等）。aiohttp 不读宿主 env，故显式取 env。
            proxy = (
                os.getenv("MARKET_FETCH_PROXY")
                or os.getenv("WP_PROXY")
                or os.getenv("HTTPS_PROXY")
                or os.getenv("https_proxy")
            )
            try:
                results["fed_funds_rate"] = await _fetch_fed_funds_rate(proxy=proxy)
            except Exception as e:
                logger.debug("fed rate fetch failed: %s", e)
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
