"""量化分析用的资产类别收益率矩阵（真实行情，非演示数据）。

数据源：腾讯 fqkline 日线接口（与 /api/stock/kline 同一通道，qfq 前复权）。
用宽基指数 / 行业 ETF 作为资产类别代理，构造 (T, N) 日收益率矩阵，
供 CVaR / Markowitz / Monte Carlo / MPC 四个 quant 模块共用。

不引入新依赖；缓存只留在进程内（TTL），不落盘。
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass

import aiohttp
import numpy as np
import pandas as pd

from ..web.aiohttp_session import async_get

# 资产类别代理：覆盖用户持仓的主要类别（A 股 / 美股 / 港股 / 黄金 / 债券）。
# 顺序即 API 返回的资产顺序，改名时前端图表按 name 匹配、不依赖顺序。
ASSET_PROXIES: tuple[tuple[str, str], ...] = (
    ("沪深300", "sh000300"),
    ("中证500", "sh000905"),
    ("创业板指", "sz399006"),
    ("黄金ETF", "sh518880"),
    ("国债ETF", "sh511010"),
    ("纳指ETF", "sh513100"),
    ("标普500ETF", "sh513500"),
    ("恒生ETF", "sh159920"),
)

_URL = "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
_HEADERS = {
    "Referer": "http://gu.qq.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}
_TTL_SECONDS = 600  # 行情日内变化，10 分钟足够；避免每次请求打 8 次外部接口

_CACHE: dict[int, tuple[float, QuantDataset]] = {}


@dataclass(frozen=True)
class QuantDataset:
    """量化分析的输入数据集。"""

    returns: pd.DataFrame  # index=date, columns=资产名, values=单期（日）收益率
    names: list[str]
    start_date: str
    end_date: str
    periods: int
    source: str = "腾讯行情 qfq 日线（资产类别代理）"


async def _fetch_close_series(name: str, code: str, count: int) -> pd.Series | None:
    """拉单个标的的收盘价序列；失败返回 None（由调用方剔除该资产）。"""
    # param 必须 6 段：code,day,,,count,qfq；7 段会被腾讯判为 param error。
    params = {"param": f"{code},day,,,{count},qfq", "r": str(int(time.time() * 1000))}
    try:
        async with await async_get(_URL, params=params, headers=_HEADERS, timeout=10) as response:
            if response.status != 200:
                return None
            text = await response.text()
            start = text.find("{")
            if start < 0:
                return None
            payload = json.loads(text[start:])
            if payload.get("code") != 0:
                return None
            data = payload.get("data", {})
            stock = data.get(code, {}) if isinstance(data, dict) else {}
            if not isinstance(stock, dict):
                return None
            rows = stock.get("qfqday") or stock.get("day") or []
            if not isinstance(rows, list):
                return None
            dates: list[str] = []
            closes: list[float] = []
            for row in rows:
                if not isinstance(row, (list, tuple)) or len(row) < 3:
                    continue
                try:
                    value = float(row[2])
                except (TypeError, ValueError):
                    continue
                if np.isfinite(value) and value > 0:
                    dates.append(str(row[0]))
                    closes.append(value)
            if len(dates) < 30:
                return None
            return pd.Series(closes, index=pd.Index(dates, name="date"), name=name, dtype=float)
    except (ValueError, KeyError, TypeError, OSError, asyncio.TimeoutError, aiohttp.ClientError):
        # ClientPayloadError / ClientResponseError 不是 OSError 子类：分块读取失败等
        # 网络异常必须在此剔除单个资产，不能让它击穿 gather 导致四个端点全 500。
        return None


async def _build(count: int) -> QuantDataset:
    """并行拉取所有代理标的，按共同交易日对齐后算日收益率。"""
    series_list = await asyncio.gather(
        *(_fetch_close_series(name, code, count) for name, code in ASSET_PROXIES)
    )
    valid = [series for series in series_list if series is not None]
    if len(valid) < 2:
        raise RuntimeError("行情源不可用：有效资产不足 2 个，无法做组合分析")

    closes = pd.concat(valid, axis=1, join="inner").sort_index()
    returns = closes.pct_change(fill_method=None).dropna(how="any")
    if len(returns) < 30:
        raise RuntimeError("共同交易日不足 30 天，无法构造收益率矩阵")

    return QuantDataset(
        returns=returns,
        names=list(returns.columns),
        start_date=str(returns.index[0]),
        end_date=str(returns.index[-1]),
        periods=len(returns),
    )


async def load_returns(count: int = 260) -> QuantDataset:
    """获取收益率矩阵，命中 10 分钟进程内缓存则直接返回。"""
    now = time.monotonic()
    cached = _CACHE.get(count)
    if cached and now - cached[0] < _TTL_SECONDS:
        return cached[1]
    dataset = await _build(count)
    _CACHE[count] = (now, dataset)
    return dataset
