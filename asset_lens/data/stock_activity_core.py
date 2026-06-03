import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from ..config import config
from .providers.cache import UnifiedCache

logger = logging.getLogger(__name__)


@dataclass
class ActivityMetrics:
    avg_turnover_rate: float = 0.0
    avg_change_percent: float = 0.0
    avg_volume: float = 0.0
    avg_amount: float = 0.0
    up_count: int = 0
    down_count: int = 0
    flat_count: int = 0
    total_count: int = 0
    activity_score: float = 0.0


@dataclass
class ETFPrediction:
    etf_name: str
    etf_code: str
    current_price: float = 0.0
    predicted_price: float = 0.0
    predicted_change: float = 0.0
    confidence: float = 0.0
    trend: str = "neutral"
    activity_score: float = 0.0
    up_ratio: float = 0.0
    down_ratio: float = 0.0
    related_stocks: list[dict[str, Any]] = field(default_factory=list)
    top_gainers: list[dict[str, Any]] = field(default_factory=list)
    top_losers: list[dict[str, Any]] = field(default_factory=list)


StockFilterCallable = Callable[[dict[str, Any]], bool]

INDEX_FUND_MAPPING: dict[str, dict[str, Any]] = {
    "沪深300": {
        "codes": ["sh510300", "sz159919"],
        "index_keys": ["SHComp", "CSI300"],
        "description": "沪深300指数基金",
    },
    "中证500": {
        "codes": ["sh510500", "sz159922"],
        "index_keys": ["CSI500"],
        "description": "中证500指数基金",
    },
    "创业板": {
        "codes": ["sz159915", "sz159948"],
        "index_keys": ["ChiNext"],
        "description": "创业板指数基金",
    },
    "科创50": {
        "codes": ["sh588000", "sh588080"],
        "index_keys": ["STAR50"],
        "description": "科创50指数基金",
    },
    "上证50": {
        "codes": ["sh510050", "sh510100"],
        "index_keys": ["SSE50"],
        "description": "上证50指数基金",
    },
}

ETF_MAPPING: dict[str, dict[str, Any]] = {
    "新能源": {
        "codes": ["sz516160", "sh515790"],
        "description": "新能源ETF",
        "stocks_filter": lambda s: any(k in s.get("name", "") for k in ["新能源", "锂电", "光伏", "风电", "储能"]),
        "weight": "equal",
        "type": "industry",
    },
    "半导体": {
        "codes": ["sz512480", "sh512760"],
        "description": "半导体ETF",
        "stocks_filter": lambda s: any(k in s.get("name", "") for k in ["半导体", "芯片", "集成电路"]),
        "weight": "equal",
        "type": "industry",
    },
    "医药": {
        "codes": ["sz159929", "sh512010"],
        "description": "医药ETF",
        "stocks_filter": lambda s: any(k in s.get("name", "") for k in ["医药", "生物", "医疗", "制药"]),
        "weight": "equal",
        "type": "industry",
    },
    "消费": {
        "codes": ["sz159928", "sh510150"],
        "description": "消费ETF",
        "stocks_filter": lambda s: any(k in s.get("name", "") for k in ["消费", "食品", "饮料", "家电", "零售"]),
        "weight": "equal",
        "type": "industry",
    },
    "军工": {
        "codes": ["sz512660", "sh512680"],
        "description": "军工ETF",
        "stocks_filter": lambda s: (
            any(
                k in s.get("name", "")
                for k in ["军工", "航天", "兵器", "中航", "航发", "航空动力", "航空工业", "沈飞", "成飞", "西飞"]
            )
            and not any(
                k in s.get("name", "")
                for k in [
                    "南方航空",
                    "东方航空",
                    "中国国航",
                    "海南航空",
                    "吉祥航空",
                    "春秋航空",
                    "厦门航空",
                    "航空股份",
                ]
            )
        ),
        "weight": "equal",
        "type": "industry",
    },
}


def load_market_stocks(cache_path: Path | None = None) -> list[dict[str, Any]]:
    cache_path = cache_path or config.cache_path
    cache = UnifiedCache(cache_dir=cache_path)
    data = cache.load_file("market_stocks.json")
    if data is not None:
        return cast(list[dict[str, Any]], data.get("data", []))
    return []


def analyze_activity(stocks: list[dict[str, Any]]) -> ActivityMetrics:
    if not stocks:
        return ActivityMetrics()

    total_turnover = 0.0
    total_change = 0.0
    total_volume = 0.0
    total_amount = 0.0
    up_count = 0
    down_count = 0
    flat_count = 0

    for stock in stocks:
        change = stock.get("change_percent", 0)
        turnover = stock.get("turnover_rate", 0)
        volume = stock.get("volume", 0)
        amount = stock.get("amount", 0)

        total_turnover += turnover
        total_change += change
        total_volume += volume
        total_amount += amount

        if change > 0.5:
            up_count += 1
        elif change < -0.5:
            down_count += 1
        else:
            flat_count += 1

    count = len(stocks)
    avg_turnover = total_turnover / count if count > 0 else 0
    avg_change = total_change / count if count > 0 else 0

    activity_score = _calculate_activity_score(avg_turnover, avg_change, up_count, down_count, count)

    return ActivityMetrics(
        avg_turnover_rate=avg_turnover,
        avg_change_percent=avg_change,
        avg_volume=total_volume / count if count > 0 else 0,
        avg_amount=total_amount / count if count > 0 else 0,
        up_count=up_count,
        down_count=down_count,
        flat_count=flat_count,
        total_count=count,
        activity_score=activity_score,
    )


def _calculate_activity_score(
    avg_turnover: float,
    avg_change: float,
    up_count: int,
    down_count: int,
    total: int,
) -> float:
    turnover_score = min(avg_turnover * 5, 30)
    change_score = min(abs(avg_change) * 3, 20)
    direction_score = abs(up_count - down_count) / total * 30 if total > 0 else 0
    participation_score = min((up_count + down_count) / total * 20 if total > 0 else 0, 20)
    return min(turnover_score + change_score + direction_score + participation_score, 100)


def _calculate_confidence(metrics: ActivityMetrics, stock_count: int) -> float:
    count_score = min(stock_count / 50 * 30, 30)
    activity_score = min(metrics.activity_score / 100 * 40, 40)
    direction_score = 30 - abs(metrics.up_count - metrics.down_count) / max(metrics.total_count, 1) * 30
    return min(count_score + activity_score + direction_score, 100)
